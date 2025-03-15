import os, time, shutil, argparse, logging
from config import DEST_DIR, SRC_DIR, TAXCO_REPORT_PATH, CONTENT_REPORT_PATH, DATASET
from files.dataset import parseDatasetFile
from files.parse import parseMarkdownFiles
from files.images import fillFailedImages
from report.populate import populateTaxcoReport, populateContentReport
from report.generateTaxcoReport import generateTaxcoReport
from report.generateContentReport import generateContentReport

class ContentCompiler:
    # Sets up skipLinkCheck and logging
    # The skipLinkCheck when set to true will not check for invalid links in the content
    def __init__(self, skipLinkCheck: bool = False):
        self.skipLinkCheck = skipLinkCheck
        self.setupLogging()

    @staticmethod
    def setupLogging() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    # Validates is the path of both the dataset and src directory are present, else it will raise an error
    def validatePaths(self, dataset, src_dir) -> None:
        if not os.path.exists(dataset):
            raise FileNotFoundError(f"Dataset file {dataset} not found.")
        if not os.path.exists(src_dir):
            raise FileNotFoundError(f"Source directory {src_dir} not found.")

    # Will remove the current destination directory if present, and make a new empty directory
    def initializeDestDir(self, dest_dir) -> None:
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.mkdir(dest_dir)


    # This function does the following:
    #   - sets all the relevant file paths
    #   - validates the file paths and makes a clean destination directory
    #   - parses the dataset 
    #   - populates both reports with the data from the dataset
    #   - parses the markdown files
    #   - fills the failed images list
    #   - generates both reports with the updated data from the compiled/parsed files
    # If during this process any error comes up, the process is stopped and exited with an error log
    def compile(self) -> None:
        try:
            dataset = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', DATASET))
            src_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', SRC_DIR))
            dest_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', DEST_DIR))
            taxco_report_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', TAXCO_REPORT_PATH))
            content_report_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', CONTENT_REPORT_PATH))
            
            self.validatePaths(dataset, src_dir)
            self.initializeDestDir(dest_dir)
            
            logging.info("Starting content compilation...")
            
            parseDatasetFile(dataset)
            logging.info("Dataset parsed successfully")
            
            populateTaxcoReport()
            populateContentReport()
            logging.info("Reports populated")
            
            parseMarkdownFiles(src_dir, dest_dir, self.skipLinkCheck)
            logging.info("Markdown files parsed")
            
            fillFailedImages(src_dir, dest_dir)
            logging.info("Failed images processed")
            
            generateTaxcoReport(taxco_report_path)
            generateContentReport(content_report_path)
            logging.info("Reports generated successfully")
            
        except Exception as e:
            logging.error(f"Error during compilation: {str(e)}", exc_info=True)
            raise

# Main process that initiates the compilling process. This function gets called when the commando is run to compile
def main() -> None:
    parser = argparse.ArgumentParser(description="Compile content script.")
    parser.add_argument('--skip-link-check', required=False, action='store_true', help='Skip link check in markdown files.')
    args = parser.parse_args()

    startTime = time.time()
    
    try:
        compiler = ContentCompiler(skipLinkCheck=args.skip_link_check)
        compiler.compile()
    except Exception as e:
        logging.error(f"Compilation failed: {str(e)}")
        exit(1)
    finally:
        elapsedTime = time.time() - startTime
        logging.info(f"Execution time: {elapsedTime:.2f} seconds")

if __name__ == "__main__":
    main()
