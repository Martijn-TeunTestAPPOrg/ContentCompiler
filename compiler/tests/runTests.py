# Imports
from pathlib import Path
import shutil, os, sys, logging, re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Variables and functions
from config import failedFiles
from files.images import fillFailedImages
from report.generateTaxcoReport import generateTaxcoReport
from report.generateContentReport import generateContentReport
from files.parse import parseMarkdownFiles
from files.dataset import parseDatasetFile
from report.populate import populateTaxcoReport, populateContentReport

class TestRunner:
    # Sets up the paths and logging
    def __init__(self):
        self.setupPaths()
        self.setupLogging()

    # Configures the logging
    @staticmethod
    def setupLogging() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    # Sets up all the necessary paths for the testing process
    def setupPaths(self) -> None:
        self.SRC_DIR = Path(__file__).resolve().parents[0] / 'test_cases'
        self.DEST_DIR = Path(__file__).resolve().parents[0] / 'test_cases_build'
        self.DATASET = Path(__file__).resolve().parents[0] / 'test_dataset.xlsx'
        self.TAXCO_REPORT_PATH = Path(__file__).resolve().parents[0] / 'reports/actual_taxco_test_report.md'
        self.CONTENT_REPORT_PATH = Path(__file__).resolve().parents[0] / 'reports/actual_content_test_report.md'
        self.EXPECTED_TAXCO_TEST_REPORT_PATH = 'tests/reports/expected_taxco_test_report.md'
        self.ACTUAL_TAXCO_TEST_REPORT_PATH = 'tests/reports/actual_taxco_test_report.md'
        self.EXPECTED_CONTENT_TEST_REPORT_PATH = 'tests/reports/expected_content_test_report.md'
        self.ACTUAL_CONTENT_TEST_REPORT_PATH = 'tests/reports/actual_content_test_report.md'


    # Validates a testreport by comparing the expected report against the actual report
    def validateTestReport(self, expected: str, actual: str) -> bool:
        # Helper function to accept both / and \ in file paths when tests are executed on different operating systems 
        def normalize_table_paths(text: str) -> str:
            normalized_lines = []
            
            # Checks the report for all lines where a table is used ( with | ) 
            # If it does, it changes the \ to /
            #   - lambda makes sure it only takes the file path out of the line
            for line in text.splitlines():
                if "|" in line: 
                    line = re.sub(r'(\S*\\\S*)', lambda m: m.group(1).replace("\\", "/"), line)
                normalized_lines.append(line)
            
            return "\n".join(normalized_lines)
        
        # Sets up the report path of the expected and actual reports
        expectedTestReportPath = Path(__file__).resolve().parents[1] / expected
        actualTestReportPath = Path(__file__).resolve().parents[1] / actual
        
        # This reads both files after being normalized into a string
        with open(expectedTestReportPath, 'r', encoding='utf-8') as f1, open(actualTestReportPath, 'r', encoding='utf-8') as f2:
            expectedTestReportContent = normalize_table_paths(f1.read())
            actualTestReportContent = normalize_table_paths(f2.read())

        # Returns true when both the expected and actual report are exactly the same
        return expectedTestReportContent == actualTestReportContent

    # Validates if all the draft files in build are the correct amount
    def validateDraft(self) -> bool:
        # Since all failed files will receive the draft = true variable, it will be the expected amount of draft files
        expectedAmountOfDraftFiles = len(failedFiles)
        actualAmountOfDraftFiles = 0
        
        # Loops over all files in the failed files list, since those will be the only ones containing a draft = true
        for file in failedFiles:
            # Gets the full path of the file to be able to read the content inside the file
            fullPath = "compiler/tests/test_cases_build/" + file['path']
            try:
                with open(fullPath, 'r', encoding='utf-8') as file:
                    # Loops over each line in the file to find a line starting with draft
                    # If it does, it will check if the value is true and if it is, it will up the counter of draft files by 1
                    for line in file:
                        if line.strip().startswith('draft:'):
                            draft_value = line.strip().split(':', 1)[1].strip().lower()
                            if draft_value == 'true':
                                actualAmountOfDraftFiles += 1
                            break
            except FileNotFoundError:
                logging.error(f"Error: The file at '{fullPath}' does not exist.")
            except Exception as e:
                logging.error(f"An error occurred: {e}")

        # returns a boolean if the draft files in actual and expected are the same    
        return expectedAmountOfDraftFiles == actualAmountOfDraftFiles

    # Validates is the path of both the dataset and src directory are present, else it will raise an error
    def validatePaths(self) -> None:
        if not os.path.exists(self.DATASET):
            raise FileNotFoundError(f"Dataset file {self.DATASET} not found.")
        if not os.path.exists(self.SRC_DIR):
            raise FileNotFoundError(f"Source directory {self.SRC_DIR} not found.")

    # Will remove the current destination directory if present, and make a new empty directory
    def initializeDestDir(self) -> None:
        if os.path.exists(self.DEST_DIR):
            shutil.rmtree(self.DEST_DIR)
        os.mkdir(self.DEST_DIR)

    # Returns the amount of markdown files in a folder
    def checkMarkdownFilesCount(self, folderPath) -> int:
        return len(list(folderPath.glob("*.md")))
    
    # Checks if the amount of files in the source directory are the same amount as the destination directory, so no files get lost during the compiling
    def evaluateTests(self) -> bool:
        #Sets up the source and destination directories
        srcDir = Path(__file__).resolve().parents[2] / 'content'
        destDir = Path(__file__).resolve().parents[2] / 'temp_build'

        # If the destination directory exists, remove the content and make a new empty one
        if os.path.exists(destDir):
            shutil.rmtree(destDir)
            os.mkdir(destDir)
        
        #Parses the markdown files in the source directory and outputs it in the destination directory
        parseMarkdownFiles(srcDir, destDir, True)

        # Checks if the amount of files are the same in both directories
        markdownCountCheck = self.checkMarkdownFilesCount(srcDir) == self.checkMarkdownFilesCount(destDir)

        # Removes the destination directory 
        shutil.rmtree(destDir) 

        # Returns a boolean values if the amount of files are equal or not
        return markdownCountCheck 

    # Executes all the tests including:
    #   - Test to validate the taxco report
    #   - Test to validate the content report
    #   - Test to validate the amount of files are correct in the build directory
    #   - Test to validate the draft files
    # Each test has its own exit code if an error occurs, so it can be traced back where the test went wrong
    def executeTests(self) -> None:
        if not self.validateTestReport(self.EXPECTED_TAXCO_TEST_REPORT_PATH, self.ACTUAL_TAXCO_TEST_REPORT_PATH):
            logging.error("Taxco Test report validation failed")
            sys.exit(11)

        if not self.validateTestReport(self.EXPECTED_CONTENT_TEST_REPORT_PATH, self.ACTUAL_CONTENT_TEST_REPORT_PATH):
            logging.error("Content Test report validation failed")
            sys.exit(12)

        if not self.evaluateTests():
            logging.error("Test evaluation failed")
            sys.exit(13)

        if not self.validateDraft():
            logging.error("Draft test failed")
            sys.exit(14)

        logging.info("Testing completed successfully")
        sys.exit(0)

    # This function does the following:
    #   - validates the file paths and makes a clean destination directory
    #   - parses the dataset 
    #   - populates both reports with the data from the dataset
    #   - parses the markdown files
    #   - fills the failed images list
    #   - generates both reports with the updated data from the compiled/parsed files
    #   - Executes the tests
    # If during this process any error comes up, the process is stopped and exited with an error log
    def run(self) -> None:
        try:
            self.validatePaths()
            self.initializeDestDir()
            
            logging.info("Starting test execution...")
            
            parseDatasetFile(self.DATASET)
            logging.info("Dataset parsed successfully")
            
            populateTaxcoReport()
            populateContentReport()
            logging.info("Reports populated")
            
            parseMarkdownFiles(self.SRC_DIR, self.DEST_DIR, False)
            logging.info("Markdown files parsed")
            
            fillFailedImages(self.SRC_DIR, self.DEST_DIR)
            logging.info("Failed images processed")
            
            generateTaxcoReport(self.TAXCO_REPORT_PATH)
            generateContentReport(self.CONTENT_REPORT_PATH)
            logging.info("Reports generated")

            self.executeTests()
                
        except Exception as e:
            logging.error(f"Error during test execution: {str(e)}")
            raise

# Main process that initiates the testing process. This function gets called when the commando is run to test
# In this function, the necessary file paths are set by the __init__ function
def main() -> None:
    try:
        runner = TestRunner()
        runner.run()
    except Exception as e:
        logging.error(f"Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()