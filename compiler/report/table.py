# Generate a markdown table string from a list of rows and headers.
def generateMarkdownTable(headers, rows):
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for row in rows:
        table += "| " + " | ".join(row) + " |\n"
    return table

# Create a new row in the file report based on the status, file path, taxonomie, and tags.
def createFileReportRow(status, filePath, srcDir, taxonomie, tags, errors):
    return {
        "status": status,
        # .stem only takes the last part of the filepath, being the file name
        "file": filePath.stem,
        # This only takes the file path from the srcDir onwards
        "path": str(filePath.relative_to(srcDir)),
        "taxonomie": '<br>'.join(taxonomie) if taxonomie else "N/A",
        "tags": '<br>'.join(tags) if tags else "N/A",
        "errors": '<br>'.join(errors) if errors else "N/A"
    }

# Format the success or failed report table based on a list.
def formatFileReportTable(fileReport):
    headers = ["Status", "File", "Path", "Taxonomie", "Tags", "Errors"]
    rows = [[
        file['status'], 
        file['file'], 
        file['path'], 
        file['taxonomie'], 
        file['tags'],
        file['errors']
     ] for file in fileReport]

    return generateMarkdownTable(headers, rows)

# Create a row for the image report table
def createImageTableTow(status, filePath, srcDir, error):
    return {
        "status" : status,
        # .stem only takes the last part of the filepath, being the file name
        "image": filePath.stem,
        # This only takes the file path from the srcDir onwards
        "path": str(filePath.relative_to(srcDir)),
        "error": error,
    }

# Format the image report table with specific headers and rows
def formatImageReportTable(imageReport):
    headers = ["Status", "Image", "Path", "Error"]
    rows = [[
        file['status'], 
        file['image'], 
        file['path'],
        file['error']
    ] for file in imageReport]

    return generateMarkdownTable(headers, rows)
