import re, logging
from config import dataset, contentReport
from config import PROCES_COL, PROCESSTAP_COL, TC1_COL, TC2_COL, TC3_COL, TAXONOMIE_PATTERN, TODO_PATTERN, ERROR_INVALID_TAXCO, ERROR_NO_TAXCO_FOUND, ERROR_TAXCO_NOT_FOUND, ERROR_TAXCO_NOT_NEEDED
from report.generateTaxcoReport import updateProcessReportData, updateSubjectReportData



# Generate tags based on the taxonomie values
# Args:
#   - taxonomies (list): List of taxonomie values.
#   - existingTags (list): List of existing tags.
#   - filePath (str): Path to the markdown file being processed.
def generateTags(taxonomies, existingTags, filePath):
    tags = []
    errors = []
    combinedTags = []
    taxonomieTags = []

    # Checks if no taxonomie code is present. This can have 4 different variants
    if taxonomies is not None and taxonomies != ['None'] and taxonomies != [''] and taxonomies != []:
        for taxonomie in taxonomies:
            # Check if the taxonomie is in the correct format
            if not re.match(TAXONOMIE_PATTERN, taxonomie):
                errors.append(f"{ERROR_INVALID_TAXCO} `{taxonomie}`")
                logging.warning(f"{ERROR_INVALID_TAXCO} `{taxonomie}` in bestand: {filePath}")
                continue

            # Split the taxonomie in it's different parts
            extractedTC1, extractedTC2, extractedTC3, extractedTC4 = splitTaxonomie(taxonomie)
            
            # If the parts are all valid
            if extractedTC1 and extractedTC2 and extractedTC3 and extractedTC4:
                # Loop trough every row in the dataset
                for row in dataset:
                    # Check if the first part of the taxonomie is equal to the TC1 column
                    if row[TC1_COL] == extractedTC1:                        
                        # Check if the second part of the taxonomie is equal to the TC2 column
                        if row[TC3_COL] in contentReport and row[TC3_COL] == extractedTC3:
                            # Adds the HBO-i/niveau tag
                            newTag = "HBO-i/niveau-" + extractedTC2
                            # Adds the HBO-i/niveau tag if it is not already yet
                            if newTag not in tags:
                                tags.append(newTag)
                            # Adds the proces tag if it is not present yet
                            if row[PROCES_COL] not in tags:
                                tags.append(row[PROCES_COL])

                            # Adds the processtap tag if it is not present yet
                            if row[PROCESSTAP_COL] not in tags:
                                tags.append(row[PROCESSTAP_COL])

                            # Adds the subject tag if it is not present yet
                            if row[TC3_COL] not in tags:
                                tags.append(row[TC3_COL])
                                
                            # Add the full taxonomie code as a taxonomie tag if it is not present yet.
                            if taxonomie not in taxonomieTags:
                                taxonomieTags.append(taxonomie)

                            # Adds a error to the file if the taxonomie code is not needed on the given HBO-i niveau
                            splittedRow =  row[TC2_COL].split(',')
                            if splittedRow[int(extractedTC2)-1] == "X": 
                                errors.append(f"{ERROR_TAXCO_NOT_NEEDED} `{taxonomie}`")
                                logging.warning(f"{ERROR_TAXCO_NOT_NEEDED} `{taxonomie}` in bestand: {filePath}")

                            # Update the process report data with the new values
                            # This is needed so the report has the correct data
                            # Before the script runs it pre-fills the report with all the taxonomie codes
                            # This is done so the report has all the taxonomie codes even if they are not used
                            # After this the report is updated with the correct data
                            updateProcessReportData(extractedTC1, extractedTC2)
                            updateSubjectReportData(extractedTC1, extractedTC2, extractedTC3, extractedTC4)

            # If no tags were found, add an error
            if tags == [] and not errors:
                errors.append(f"{ERROR_TAXCO_NOT_FOUND} `{taxonomie}`")   
                logging.warning(f"{ERROR_TAXCO_NOT_FOUND} `{taxonomie}` in bestand: {filePath}")
    else:
        # If no taxonomie code was found, add an error
        errors.append(f"{ERROR_NO_TAXCO_FOUND}")
        logging.warning(f"{ERROR_NO_TAXCO_FOUND} in bestand: {filePath}")

    # Combine the existing tags with the new tags and taxonomieTags
    combinedTags.extend(existingTags or [])
    combinedTags.extend(tags or [])
    combinedTags.extend(taxonomieTags or [])
    
    # Sort combined_tags so that "HBO-i/niveau-" tags are moved to the start
    combinedTags = sorted(combinedTags, key=lambda tag: (not tag.startswith("HBO-i/niveau-"), tag))

    # Makes a dictionary so all duplicate items are removed and sets it as a list. Returns the new list and errors
    return list(dict.fromkeys(combinedTags)), errors

def splitTaxonomie(taxonomie):
    return taxonomie.split('.')

# Helper function to extract specific values from the page properties / header values of a markdown file
def extractHeaderValues(content, fieldName):
    # Puts all the different lines from the content of a file into a list
    lines = content.splitlines()
    values = []

    # Loops over the lines. Enumerate is used to have both an index and a the value of the line
    for i, line in enumerate(lines):
        # Only looking at the lines where this page property / header value is present
        if line.startswith(f'{fieldName}:'):
            # This is for the case where there is a single value after the :
            # Checks:
            #   - if there is a : in the line and 
            #   - that the value after the : has more characters than 0 after removing the leading and trailing whitespaces
            if ':' in line and len(line.split(':', 1)[1].strip()) > 0:
                # Adds the value after the :
                values.append(line.split(':', 1)[1].strip()) 
            else:
                # This skips the first item (+ 1) since this will contain the header / page property and the :. 
                # The values for this header / page property will come on the following lines
                for j in range(i + 1, len(lines)):
                    # This loop continues for all the lines that start with - after being stripped of whitespaces (leading & trailing)
                    # The first subline that doesnt start with a - will cut off the loop with the break 
                    subLine = lines[j].strip()
                    if subLine.startswith('- '):
                        values.append(subLine.lstrip('- ').strip())
                    else:
                        break
            # This makes sure only the first occurance of a page property / header value is looked at
            break

    return values if values else None

# Helper function to find all the To-Do items in the content of a markdown file.
# WIP = Work-In-Progress	
def findWIPItems(content):
    return re.findall(TODO_PATTERN, content)

# Helper function to check if a file has an ignore tag.
def hasIgnoreTag(content, filePath):
    ignoreTAG = extractHeaderValues(content, 'ignore')

    # Checks if ignoreTag is present and also has the true value
    if ignoreTAG and "true" in ignoreTAG:
        logging.info(f"File has an ignore tag, ignoring file: {filePath}")
        return True

    return False
