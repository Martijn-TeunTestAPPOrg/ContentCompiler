import re, os, logging
from pathlib import Path
from config import VALID_DYNAMIC_LINK_PREFIXES, ERROR_INVALID_DYNAMIC_LINK


# Update dynamic links in the content of a markdown file.
def updateDynamicLinks(filePath, content, skipValidateDynamicLinks):
    # Find all dynamic links in the content
    dynamicLinks = re.findall(r'\[\[[^"\[][^]]*?\]\]', content)

    errors = []
    
    for link in dynamicLinks:
        cleanedLink = link.strip('[[]]')
        
        # Skip links that start with any of the valid prefixes
        if any(cleanedLink.startswith(prefix) for prefix in VALID_DYNAMIC_LINK_PREFIXES):
            continue
        
        # Remove 'content/' because in production the content is not in the 'content' folder but in the root of the build folder
        newLink = link.replace('content/', '')
        
        # Replace the old link with the new link in the content
        content = content.replace(link, newLink)
        
        # Skip dynamic link check if flag is set
        # This is used in the PR validation check when only updated the content is being checked and the links will not be checked
        if(skipValidateDynamicLinks):
            continue

        # Check if the dynamic link is valid and add an error if it is not a valid link
        if not validateDynamicLink(filePath, newLink):
            reportLink = newLink.replace('|', '\|')
            errors.append(f"{ERROR_INVALID_DYNAMIC_LINK} `{reportLink}`")
            logging.warning(f"{ERROR_INVALID_DYNAMIC_LINK} `{newLink}` in bestand: {filePath}")

    return content, errors

# Checks if the dynamic link is valid and the file exists.
def validateDynamicLink(sourceFilePath, link):
    # Define the root content directory (assuming it is one level up from the current script)
    contentPath = sourceFilePath
    while Path(contentPath).name != 'content' and Path(contentPath).name != 'test_cases':
        contentPath = contentPath.parent
    
    # Verify that contentPath exists
    if not contentPath.exists():
        logging.warning(f"Error: Content path '{contentPath}' does not exist.")
        return False

    # Clean up the link by removing the surrounding [[ and ]]
    cleanedLink = link.strip('[[]]')

    # If the link contains a section (anchor), split the link at '#'
    if '#' in cleanedLink:
        # Use only the part before '#'
        cleanedLink = cleanedLink.split('#')[0]  

    # Parse the base name from the cleaned link
    linkParts = cleanedLink.split('|')
    fileName = linkParts[0].strip().split('/')[-1]

    # Search for the file in all subdirectories within 'content' using os.walk
    foundFile = None
    for root, dirs, files in os.walk(contentPath):
        for file in files:
            if file.startswith(fileName):
                # If the file is found, the link is valid, so break the loop
                return True

    # If no valid file is found, report error with details
    if not foundFile:
        logging.warning(f"Error: source file: {sourceFilePath}, target file '{fileName}' not found in content.")

    return False
