"""
Given a Google Drive/Dropbox link to a PDF, it will download the PDF, compress the PDF, and upload it to DocumentCloud. 
"""
import os
import shutil
import subprocess
from documentcloud.addon import AddOn
from clouddl import grab

class Compress(AddOn):
    """ Downloads the file, runs Ghostscript to compress the file, and uploads to DocumentCloud if file is <500MB"""
    def check_permissions(self):
        """The user must be a verified journalist to upload a document"""
        self.set_message("Checking permissions...")
        user = self.client.users.get("me")
        if not user.verified_journalist:
            self.set_message(
                "You need to be verified to use this add-on. Please verify your "
                "account here: https://airtable.com/shrZrgdmuOwW0ZLPM"
            )
            sys.exit()
            
    def fetch_files(self, url):
        """Fetch the files from either a cloud share link or any public URL"""
        self.set_message("Retrieving EML/MSG files...")
        os.makedirs(os.path.dirname("./out/"), exist_ok=True)
        downloaded = grab(url, "./out/")
    
    def compress_pdf(self, file_name):
        bash_cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=/screen -dNOPAUSE -dQUIET -dBATCH -sOutputFile={file_name}-compressed.pdf {file_name}.pdf; rm {file_name}.pdf"
        subprocess.call(bash_cmd, shell=True)
        
    def main(self):
        """The main add-on functionality goes here."""
        url = self.data.get("url")
        self.check_permissions()
        self.fetch_files(url)
        successes = 0
        errors = 0
        for current_path, folders, files in os.walk("./out/"):
            for file_name in files:
                file_name = os.path.join(current_path, file_name)
                self.set_message("Attempting to compress PDF files")
                abs_path = os.path.abspath(file_name)
                try:
                    self.compress_pdf(abs_path)
                except RuntimeError as re:
                    self.send_mail("Runtime Error for Email Conversion AddOn", "Please forward this to info@documentcloud.org \n" + str(re))
                    errors += 1
                    continue
                else:
                    self.set_message("Uploading compressed file to DocumentCloud...")
                    file_name_no_ext = os.path.splitext(abs_path)[0]
                    self.client.documents.upload(f"{file_name_no_ext}-compressed.pdf")
                    successes += 1
        sfiles = "file" if successes == 1 else "files"
        efiles = "file" if errors == 1 else "files"
        self.set_message(f"Converted {successes} {sfiles}, skipped {errors} {efiles}")
        shutil.rmtree("./out", ignore_errors=False, onerror=None)
if __name__ == "__main__":
    Compress().main()
