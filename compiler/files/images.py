from pathlib import Path
import os, re, shutil, logging
from config import failedImages
from config import IGNORE_FOLDERS, ERROR_IMAGE_NOT_USED, ERROR_IMAGE_NOT_FOUND, TODO_ITEMS_ICON, IMAGE_PATTERN
from report.table import createImageTableTow

# Searches for images in the markdown content, copies the images from the source to the build directories, keepign the directory structure
#  
def copyImages(content, srcDir, destDir):
    errors = []
    # If a file does not contain any content, it will not be checked
    if content is None:
        return errors
    
    # Finds all the images using the IMAGE_PATTERN regex
    imageLinks = re.findall(IMAGE_PATTERN, content)
    # Checks each image link 
    for imageLink in imageLinks:
        print(imageLinks)
        # Checks if the image link is stripped, if not it will strip it
        # index 0 is an image name/file name
        # index 1 is for the alt text of an image
        # index 2 is for the image name/file name if there would be an alt text (then index 0 would be '')
        if imageLink[0]:
            imagePath = imageLink[0].strip()
        elif imageLink[2]:
            imagePath = imageLink[2].strip()

        # If there is no image path, it will continue to the next imageLink
        if not imagePath:
            continue

        # If the image is from a website (either http or https), it will continue to the next imageLink
        # This function will only check for image files inside the content, not external images from the internet
        if imagePath.startswith('http://') or imagePath.startswith('https://'):
            continue

        
        foundImagePath = None
        # Checks if it can find the image path in the source directory
        for root, dirs, files in os.walk(srcDir):
            if imagePath in files:
                foundImagePath = Path(root) / imagePath
                break
        
        # If the image path was found
        #   - Copies the image to the same folder in the destination directory
        if foundImagePath and foundImagePath.exists():
            relativePath = foundImagePath.relative_to(srcDir)
            newImagePath = destDir / relativePath
            newImagePath.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy(foundImagePath, newImagePath)
        # Else it will add an error that the image was not found
        else:
            error_msg = f"{ERROR_IMAGE_NOT_FOUND} `{imagePath}`"
            logging.warning(error_msg)
            errors.append(ERROR_IMAGE_NOT_FOUND)
    # returns the found error for a file about images
    return errors

# Fills the failed images list
def fillFailedImages(srcDir, destDir):
    # Sets up the source and destination directories
    srcDirPath = Path(srcDir).resolve()
    destDirPath = Path(destDir).resolve()
    
    # Retrieves the images in the directories
    srcImages = getImagesInFolder(srcDirPath)
    destImages = getImagesInFolder(destDirPath)

    # Per images in source checks if the it present the destination
    #   - If not, it will add it to the failed images list and add an error
    for image in srcImages: 
        if str(image.stem) not in {str(img.stem) for img in destImages}:
            error_msg = f"{ERROR_IMAGE_NOT_USED} `{image.stem}`"
            logging.warning(error_msg)
            failedImages.append(createImageTableTow(TODO_ITEMS_ICON, image, srcDirPath, ERROR_IMAGE_NOT_USED))


# Helper function to populate the image report
def getImagesInFolder(dir):
    # Looks for all folders that are named "src". This the agreed-upon name for folders containing content images
    folders = [folder for folder in Path(dir).rglob("src") if folder.is_dir()]

    # Makes a new set for the images
    images = set()

    # For each folder the following is checked:
    #   - if the folder is any of the ignored folders, it will continue to the next folder
    #   - it will add all the images found in a source folder to the images set and return the images
    for folder in folders:
        if any(ignoreFolder in str(folder) for ignoreFolder in IGNORE_FOLDERS):
            continue

        images.update(filePath for filePath in folder.rglob("*")) 
    return images
