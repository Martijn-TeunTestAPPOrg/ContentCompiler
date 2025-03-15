from report.table import generateMarkdownTable
from config import taxcoReport, contentReport, fileTypeMapping
from config import LT, DT, OI, PI, FAIL_CIRCLE_ICON, SUCCESS_ICON, NOT_NECESSARY_ICON


# Update the taxco list with the new values
def updateProcessReportData(tc1, tc2):
    # Helper function to update the TC2 status for a given index
    def updateProcessReportRow(tc1, tc2, index):
        # Check if the tc2 (HBO-i niveau) matches the index and the current status (tc2) is not NOT_NECESSARY_ICON
        if tc2 == str(index + 1) and taxcoReport[tc1]['TC2'][index] != NOT_NECESSARY_ICON:
            # Update the status to 'v' (success)
            taxcoReport[tc1]['TC2'][index] = 'v'

    # Loop through the three levels and update the process report row
    for i in range(3):
        updateProcessReportRow(tc1, tc2, i)

# Update the content list data with the new values.
def updateSubjectReportData(tc1, tc2, tc3, fileType):
    # Helper function to update a subject table row with the right values
    def updateSubjectReportRow(tc1, tc2, tc3, fileType, searchType):
        # Get the full name of a 4C/ID component if it exists in the mapping
        # Searchtype and filetype are supposed to both be 4C/ID components
        fileTypeFull = fileTypeMapping.get(fileType, fileType)
        # Sets the value of a 4C/ID component for the given tc3 (subject) and tc1 on the three different HBO-i niveaus
        # This shows if there is content present for the given subject and process + processstep on a certain 4C/ID component (searchType)
        contentReport[tc3][tc1][searchType] = [
            'v' if fileTypeFull == searchType and tc2 == '1' and contentReport[tc3][tc1][searchType][0] != NOT_NECESSARY_ICON else contentReport[tc3][tc1][searchType][0], 
            'v' if fileTypeFull == searchType and tc2 == '2' and contentReport[tc3][tc1][searchType][1] != NOT_NECESSARY_ICON else contentReport[tc3][tc1][searchType][1], 
            'v' if fileTypeFull == searchType and tc2 == '3' and contentReport[tc3][tc1][searchType][2] != NOT_NECESSARY_ICON else contentReport[tc3][tc1][searchType][2]
        ]

     # Sets the value of the tc2 value for the given tc3 (subject) and tc1 on the three different HBO-i niveaus. 
     # This shows if there is any content present for the given subject and process + processstep
    contentReport[tc3][tc1]['TC2'] = [
        'v' if tc2 == '1' and contentReport[tc3][tc1]['TC2'][0] != NOT_NECESSARY_ICON else contentReport[tc3][tc1]['TC2'][0], 
        'v' if tc2 == '2' and contentReport[tc3][tc1]['TC2'][1] != NOT_NECESSARY_ICON else contentReport[tc3][tc1]['TC2'][1], 
        'v' if tc2 == '3' and contentReport[tc3][tc1]['TC2'][2] != NOT_NECESSARY_ICON else contentReport[tc3][tc1]['TC2'][2]
    ]

    # Updates the subject report for the different 4C/ID components
    updateSubjectReportRow(tc1, tc2, tc3, fileType, LT)
    updateSubjectReportRow(tc1, tc2, tc3, fileType, OI)
    updateSubjectReportRow(tc1, tc2, tc3, fileType, PI)
    updateSubjectReportRow(tc1, tc2, tc3, fileType, DT)

# Generate the report based on the taxonomie report, success, and failed reports.
def generateTaxcoReport(reportPath):
    with open(reportPath, "w", encoding="utf-8") as f:
        # This will make sure it won't be visible in the quartz page
        f.write('---\ndraft: true\n---\n')
        
        f.write('## Rapport 1 - Processtappen\n')
        f.write('*Doel: achterhalen welke processtappen nog helemaal niet zijn geïmplementeerd*\n\n')
        f.write('- ✅ Er bestaat een bestand met deze taxonomiecode op dit niveau \n')
        f.write('- ⛔️ Er is geen enkel bestand met deze taxonomiecode op dit niveau \n')
        f.write('- 🏳️ De taxonomiecode wordt niet aangeboden op dit niveau (X in de Dataset) \n')
        f.write('\n')
        f.write(generateProcessTable())

        f.write('\n\n')

        f.write('## Rapport 2 - Onderwerpen Catalogus\n')
        f.write('*Doel: Lijst met onderwerpen + gekoppelde taxonomie code voor inzicht in aangeboden onderwerpen.*\n')
        f.write('Bij kolom *TC2*, *Leertaken*, *Ondersteunende informatie*, *Procedurele informatie* en *Deeltaken* zijn drie tekens aanwezig om de drie HBO-i niveaus weer te geven\n\n')
        f.write('- ✅ Het onderwerp met taxonomie code wordt aangeboden op het aangegeven niveau \n')
        f.write('- ⛔️ Het onderwerp met taxonomie code wordt **niet** aangeboden op het aangegeven niveau \n')
        f.write('- 🏳️ Het onderwerp hoeft met deze taxonomie code niet aangeboden te worden op het aangegeven niveau \n')
        f.write('\n')
        f.write(generateSubjectTable())

# Helper function to get the status icon for a given level
def getStatus(level):
    if level == 'v':
        return SUCCESS_ICON
    elif level == 'x':
        return FAIL_CIRCLE_ICON
    else:
        return NOT_NECESSARY_ICON
        
# Formats the report table for the process table
def generateProcessTable():
    # Define the headers for the process table
    headers = ["TC1", "Proces", "Processtap", "Niveau 1", "Niveau 2", "Niveau 3"]
    rows = []

    # Loop through the taxco report and generate the table rows
    # tc is the tc1 
    # details contains the information connected to the tc1
    for tc, details in taxcoReport.items():
        proces = details.get('Proces', '')
        processtap = details.get('Processtap', '')
        tc2_levels = details.get('TC2', {})
        niveau_1 = getStatus(tc2_levels[0])
        niveau_2 = getStatus(tc2_levels[1])
        niveau_3 = getStatus(tc2_levels[2])

        # Append the row to the list of rows
        rows.append([tc, proces, processtap, niveau_1, niveau_2, niveau_3])

    # Generate the markdown table using the headers and rows
    return generateMarkdownTable(headers, rows)

# Format the report for the subject table
def generateSubjectTable():
    headers = ["TC3", "TC1", "TC2", LT, OI, PI, DT]
    rows = []

    # Helper function to get the status for each level
    def getStatusForLevels(levels):
        return ' '.join([getStatus(level) for level in levels])

    # Loop through the content report and generate the table
    for tc3, row in contentReport.items():
        # Per tc3 (subject) look at the tc1 and the following details (others)
        for tc1, other in row.items():
            # All details are a list of three items. From others, the list with key is pulled with a * 3 for the three different HBO-i niveaus
            tc2 = getStatusForLevels(other.get('TC2', [''] * 3))
            leertaak = getStatusForLevels(other.get(LT, [''] * 3))
            ondersteunende_informatie = getStatusForLevels(other.get(OI, [''] * 3))
            procedurele_informatie = getStatusForLevels(other.get(PI, [''] * 3))
            deeltaak = getStatusForLevels(other.get(DT, [''] * 3))

            # Append the row to the list of rows
            rows.append([tc3, tc1, tc2, leertaak, ondersteunende_informatie, procedurele_informatie, deeltaak])

    # Generate the markdown table using the headers and rows
    return generateMarkdownTable(headers, rows)
