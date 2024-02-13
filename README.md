This code enables the extraction of articles from The Guardian newspaper using the API provided by the newspaper, and saves them into a PDF file. It is a Python script.

To access the API, you need to request an API key at https://bonobo.capi.gutools.co.uk/register/developer

The limitations of this application are consistent with those of similar applications, as it is confined to the content provided by The Guardian for API use. It may not include certain articles that, for an unknown reason, do not integrate into the API queries. However, for academic purposes, it can be considered that all publicly available articles for external use are made accessible while respecting copyright protection.

To use it, you should download the "code" file and install certain Python packages.

pip install requests <br>
pip install reportlab <br>
pip install beautifulsoup4 <br>
pip install xhtml2pdf <br>
