# SLT Usage Analyzer
---
A desktop webapplication for checking SLT usage build in python.
![Demo image](https://github.com/gamithaKalharaW/SLT-Usage-Analyzer/blob/master/docs/chrome_eUajhYow4o.png)

## Features
 - Automatic login and extraction of usage data.
 - Descriptive graphical representation of retrieved data.
 - Consise logging through [ loguru ](https://github.com/Delgan/loguru) package.

## Getting Started
### Dependencies
 - `python` 
 - [PowerShell](https://github.com/PowerShell/PowerShell)
 - [pipx](https://github.com/pypa/pipx)

 *SLT Usage Analyzer uses chrome browser as the default option for viewing the GUI. Other browsers can be specified in the config file.*

#### Installing via `pip`

```python
pip install git+https://github.com/gamithaKalharaW/SLT-Usage-Analyzer/tree/readme 
```
The application can be run either as a python module or as an executable script.

```python
python -m sltusageanalyzer
```
*or*
```python
sltanalyzer
```

## Configuration

The configuration file is stored at `%HOMEPATH%\.sltusageanalyzer\.analyzer.config`.

### Options
 - `BROWSER_PATH`: Path to browser. Defaults to `C:\Program Files\Google\Chrome\Application\chrome.exe`
 - Auth data(`USERNAME`, `PASSWORD`, `ID`): SLT credentials.


## TODO
 - [ ] Improve logging.
 - [ ] Add asset file validation.
 - [ ] Improve cli capabilites.
