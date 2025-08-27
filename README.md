# Yar Madness for the Summer!

This project automates the submission of forms for Black Desert Online (BDO) event registration using Playwright with proxy support.  

Ready to Duel?  
Yar Madness Returns!  
Fancy a Yar game against your fellow Adventurers?  
Join the battle arena they don't tell you about 👀  
[YAR!!!](https://www.naeu.playblackdesert.com/en-US/News/Detail?groupContentNo=8987&countryType=en-US)

## Prerequisites

* Python 3.7+
* pip (Python package installer)

## Installation

1. Clone the repository:

```bash
   git clone git@github.com:Ottitsch/yar-madness.git
   cd bdo-auto-form
   ```

2. Create a virtual environment:

```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   * On Windows:

```bash
     venv\Scripts\activate
     ```

   \* On macOS/Linux:

```bash
     source venv/bin/activate
     ```

4. Install the required packages:

```bash
   pip install playwright python-dotenv
   ```

5. Install Playwright browsers:

```bash
   playwright install chromium
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
USERNAME=your_proxy_username
PASSWORD=your_proxy_password
HOST=brd.superproxy.io
PORT=33335
REGION=Europe
HEADLESS=1
ROTATE_PER=10
BLOCK_MEDIA=1
```

### Environment Variables Explanation

* `USERNAME`: Your proxy service username
* `PASSWORD`: Your proxy service password
* `HOST`: Proxy host address
* `PORT`: Proxy port
* `REGION`: Target region (Europe or other)
* `HEADLESS`: Run browser in headless mode (1 = yes, 0 = no)
* `ROTATE_PER`: Rotate proxy after N submissions (0 = never rotate)

## Usage

1. Add the names to submit in `names.txt`, one name per line
2. Run the form submitter:

```bash
   python apply.py
   ```

3. (Optional) Test proxy connectivity:

```bash
   python proxy.py
   ```

## Files

* `apply.py`: Main script for form submission
* `proxy.py`: Proxy connectivity testing script
* `names.txt`: List of names to submit
* `.env`: Configuration file (not committed to version control)

## How It Works

The script uses Playwright to automate a Chromium browser that:

1. Loads the BDO event form page
2. Fills in the character name from names.txt
3. Selects the region
4. Generates a random Discord ID
5. Accepts consent
6. Submits the form
7. Repeats for all names in the list

Proxy support allows for rotating IP addresses to avoid detection, with configurable rotation frequency.

## Disclaimer

This tool is for educational purposes only. Use at your own risk. Automation of form submissions may violate the terms of service of the website.

