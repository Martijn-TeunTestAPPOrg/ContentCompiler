import logging
from pathlib import Path
from config import failedFiles, parsedFiles, WIPFiles, ignoredFiles
from config import ERROR_NO_TAXCO_FOUND, FAIL_CROSS_ICON, WARNING_ICON, SUCCESS_ICON, TODO_ITEMS_ICON, IGNORE_FOLDERS, ERROR_WIP_FOUND, ERROR_TAXCO_NOT_NEEDED, NOT_NEEDED_ICON, ERROR_IGNORE_TAG_USED
from files.images import copyImages
from files.links import updateDynamicLinks
from report.table import createFileReportRow
from files.markdownUtils import extractHeaderValues, generateTags, findWIPItems, hasIgnoreTag


# Update markdown files in the source directory
def parseMarkdownFiles(srcDir, destDir, skipValidateDynamicLinks):
    # .resolve() = Make the path absolute, resolving all symlinks on the way and also 
    # normalizing it (for example turning slashes into backslashes under
    # Windows). 
    #
    # This will also create the directory at the destination path
    destDirPath = Path(destDir).resolve()
    destDirPath.mkdir(parents=True, exist_ok=True)

    srcDirPath = Path(srcDir).resolve()

    # Loop through all markdown files in the source directory where the file name has .md (markdown) as file extension
    for filePath in Path(srcDirPath).rglob('*.md'):
        relativePath = filePath.relative_to(srcDirPath)
        destAndRelativePath = destDirPath / relativePath
        errors = []
        tagErrors = []
        todoItems = []
        taxonomie = []
        newTags = []
        isDraft = False
        isIgnore = False

        # Skip the folders that are saved in IGNORE_Folders
        # It checks if any folder in the IGNORE_FOLDERS list is present in the filepath
        if any(folder in str(filePath) for folder in IGNORE_FOLDERS):
            logging.info(f"Skipping folder: {filePath}")
            continue

		# Read the content of the file as a string
        with open(filePath, 'r', encoding='utf-8') as f:
            content = f.read()

		# Parse the file
        # After this process:
        #   - the dynamic links in the content will have been checked
        #   - the images will have been copied to the build folder and wrong images have been identified
        #   - existing tags will be extracted
        #   - extracts the difficulty rating if this is present.
        content, linkErrors = updateDynamicLinks(filePath, content, skipValidateDynamicLinks)
        imageErrors = copyImages(content, srcDirPath, destDirPath)
        existingTags = extractHeaderValues(content, 'tags')
        difficulty = extractHeaderValues(content, 'difficulty')


        # If content has the ignore tag, it will add an error to the file
        if hasIgnoreTag(content, filePath):
            isIgnore = True
            errors.append(ERROR_IGNORE_TAG_USED)
        else:
            # After this process:
            #   - The taxonomie codes are extracted
            #   - The new tags (with errors) will be extracted from the given taxonomie codes
            #   - The todo items in the file will be identified and if present, will be given an error
            taxonomie = extractHeaderValues(content, 'taxonomie')
            newTags, tagErrors = generateTags(taxonomie, existingTags, filePath)
            todoItems = findWIPItems(content)

            if todoItems:
                errors.append(ERROR_WIP_FOUND + "<br>" + '<br>'.join(todoItems))

        # Combine all errors
        errors = linkErrors + imageErrors + tagErrors + errors

        # If there are any errors, the file is considered a draft unless the ignore tag is used
        if errors and not isIgnore:
            isDraft = True

        # This will add the different files to the different lists and save the parsed files:
        #   - Work-In-Progress
        #   - Ignored
        #   - Failed 
        #   - Successful 
        appendFileToSpecificList(errors, todoItems, filePath, srcDirPath, taxonomie, newTags)
        saveParsedFile(filePath, taxonomie, newTags, difficulty, isDraft, isIgnore, content, destAndRelativePath)

# Fill the different lists used for the report
# To know to which report/table to add the data, each if/else statement has 2 variables, the icon and targetlist on where to add the file
def appendFileToSpecificList(errors, todoItems, filePath, srcDir, taxonomie, tags):
	if errors:
		if todoItems:
            # This will add the file to the WIP list with the todo icon
			icon, targetList = TODO_ITEMS_ICON, WIPFiles
		elif ERROR_IGNORE_TAG_USED in errors:
            # This will add the file to the Ignored list with a warning icon
			icon, targetList = WARNING_ICON, ignoredFiles
		elif ERROR_NO_TAXCO_FOUND in errors or ERROR_TAXCO_NOT_NEEDED in errors:
            # This will add the file to the Failed list with
            #   - A Cross icon in case no taxonomie code was found in a file
            #   - An orange circle in case a taxonomie code was found that was not neede
			icon, targetList = FAIL_CROSS_ICON if ERROR_NO_TAXCO_FOUND in errors else NOT_NEEDED_ICON, failedFiles
		else:
            # This will add the file to the Failed list with a warning icon
			icon, targetList = WARNING_ICON, failedFiles
	else:
        # This will add the file to the Successful file with a success icon
		icon, targetList = SUCCESS_ICON, parsedFiles

    # Add the file to the selected targetlist
	targetList.append(createFileReportRow(icon, filePath, srcDir, taxonomie, tags, errors))

# Combines everything into a new md file
def saveParsedFile(filePath, taxonomie, tags, difficulty, isDraft, isIgnore, content, destPath):
    # This will make a new page property with the given taxonomie codes, tags and title
    newContent = (
        f"---\ntitle: {filePath.stem}\ntaxonomie: {taxonomie}\ntags:\n" +
        '\n'.join([f"- {tag}" for tag in tags]) +
        "\n"
    )

    # If the difficulty page property / header value has been added, it will be re-added here
    if difficulty:
        newContent += "difficulty: " + ''.join([f"{level}" for level in difficulty]) + "\n"

    # If the draft page property / header value needs to be added, it will be set on true here, so it won't be visible
    if isDraft:
        newContent += "draft: true \n"

    # If the ignore page property / header value needs to be added, it will be set to true here, so it won't be looked at by the compiler
    if isIgnore:
        newContent += "ignore: true \n"

    # Finish off the page properties with the ---
    newContent += "---" + content.split('---', 2)[-1]

    # Creates the missing directory at the destination path
    destPath.parent.mkdir(parents=True, exist_ok=True)

    # This will make sure the new content can be written into the file
    with open(destPath, 'w', encoding='utf-8') as f:
        f.write(newContent)
