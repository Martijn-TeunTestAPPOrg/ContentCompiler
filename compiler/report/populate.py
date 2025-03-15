from config import dataset, taxcoReport, contentReport
from config import TC1_COL, TC2_COL, TC3_COL, PROCES_COL, PROCESSTAP_COL, NOT_NECESSARY_ICON, LT_COL, DT_COL, OI_COL, PI_COL, LT, DT, OI, PI

# Populates the taxco report with the data from the dataset 
# Every tc1 code is the unique identifier
def populateTaxcoReport():
    global taxcoReport

    # Check for all rows in the dataset and extract the values
    # If the tc1 is already in the taxcoReport, it will update the values
    # Else it will make a new entry of the tc1 and details
    for row in dataset:
        tc1 = row[TC1_COL]
        tc2 = row[TC2_COL]
        proces = row[PROCES_COL]
        processtap = row[PROCESSTAP_COL]

        if tc1 in taxcoReport:
            updateTaxcoReport(tc1, tc2)
        else:
            addNewTaxcoReportEntry(tc1, tc2, proces, processtap)

# Updates an existing row in the taxco report
def updateTaxcoReport(tc1, tc2):
    # Split the HBO-i niveaus up in a list
    splittedTc2 = tc2.split(',')
    # Loop over the range of the niveaus (1-3)
    for index in range(1, 3):
        # If the existing entry has a not necessary icon and the new value does not have it, it needs to be updated with the new value
        if taxcoReport[tc1]['TC2'][index] == NOT_NECESSARY_ICON and splittedTc2[index] != NOT_NECESSARY_ICON:
            taxcoReport[tc1]['TC2'][index] = splittedTc2[index]

# Adds a new row entry to the taxco report
def addNewTaxcoReportEntry(tc1, tc2, proces, processtap):
    # Split the HBO-i niveaus up in a list
    splittedTc2 = tc2.split(',')
    # Fill the report with a new row with the tc1 as key and the proces, processtap and tc2 as values
    taxcoReport[tc1] = {
        "Proces": proces,
        "Processtap": processtap,
        # If the dataset contained an X, it should give it the NOT_NECESSARY_ICON, otherwise just a small x, which means content is needed for that HBO-i niveau
        'TC2': [NOT_NECESSARY_ICON if splittedTc2[0] == 'X' else 'x', NOT_NECESSARY_ICON if splittedTc2[1] == 'X' else 'x', NOT_NECESSARY_ICON if splittedTc2[2] == 'X' else 'x']
    }

# Fills the content  report with data from the dataset
# Every combination of tc3 and tc1 are the unique combination for the content report
def populateContentReport():
    global contentReport

    # Check for all rows in the dataset and extract the values
    for row in dataset:
        tc1 = row[TC1_COL]
        tc2 = row[TC2_COL]
        tc3 = row[TC3_COL]
        lt = row[LT_COL]
        oi = row[OI_COL]
        pi = row[PI_COL]
        dt = row[DT_COL]

        # Initialize a new entry for tc3 if it doesn't exist
        if tc3 not in contentReport:
            contentReport[tc3] = {}

        # Add a new entry for tc1 under the current tc3 if it doesn't exist
        # In this list, the tc2 and all the 4C/ID components will be added as values
        if tc1 not in contentReport[tc3]:
            contentReport[tc3][tc1] = {
                'TC2': processColumn(tc2),
                LT: processColumn(lt),
                OI: processColumn(oi),
                PI: processColumn(pi),
                DT: processColumn(dt),
            }

# Processes a column of data, splitting it by commas and replacing 'X' with NOT_NECESSARY_ICON.
def processColumn(columnData):
    # If the dataset contained an X, it should give it the NOT_NECESSARY_ICON, otherwise just a small x, which means content is needed for that HBO-i niveau
    return [NOT_NECESSARY_ICON if val == 'X' else 'x' for val in columnData.split(',')]