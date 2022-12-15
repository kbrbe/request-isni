# Request ISNI

Python scripts to perform ISNI requests via a provided AtomPub API and report the outcome in CSV files.

ISNI is the [ISO 27729:2012](https://www.iso.org/standard/44292.html) standard name identifier that uniquely identifies public entities who contributed to creative works.
As an ISNI registration agency, the Royal Library of Belgium (KBR) can request ISNI identifiers from the ISNI central database. The scripts of this repository are used to perform such requests against the ISNI [AtomPub API](https://isni.org/page/technical-documentation/): each request is one XML file containing the local KBR identifier of a public entity, the response XML files are stored, and a CSV report is generated showing the outcome of the performed requests, for example the newly assigned ISNI identifiers.

## Usage

Create and activate a Python virtual environment
```bash

# Create a new Python virtual environment
python3 -m venv py-request-isni-env

# Activate the virtual environment
source py-request-isni-env/bin/activate

# Install dependencies
pip -r requirements.txt
```

Given that you have correctly formatted ISNI request XML files in the folder `my-requests`, you can call the script in the following way to obtain response XML files in the folder `my-responses` and a report at `overview.csv`.

```bash
python request_isni.py \
    --url https://isni-m.oclc.org:/ATOM/isni?
    --input-folder my-requests \
    --response-folder my-responses \
    --output-file overview.csv
```

Please note, that you should be an ISNI member to use this API. If your IP is not whitelisted you will receive HTTP error messages.

Instead of providing the URL via commandline parameter, you can also create a `.env` file with the following content: `ISNI_ATOM_URL=https://isni-m.oclc.org:/ATOM/isni?`.

## License

The license of this software was chosen using https://ufal.github.io/public-license-selector and based on licenses of software libraries used by this repo:

| Library | Description | License |
|---------|-------------|---------|
| certifi | Providing the list of Mozilla's carefully curated collection of Root certificates, such that we can communicate securely with the ISNI server via https. | [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/) |
| python-dotenv | Functionality to load a .env environment file and make the environment variables accessible in Python. We use this library to provide the functionality of specifying the ISNI API URL in an environment variable instead of via a commandline parameter. | [BSD 3-clause](https://opensource.org/licenses/BSD-3-Clause) |
| requests | We use this library to perform HTTP requests against the ISNI APIs. | [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| urllib3 | Used by the requests library to make requests, thus implicitly used to make API requests against the ISNI APIs. | [MIT](https://opensource.org/licenses/MIT) |

