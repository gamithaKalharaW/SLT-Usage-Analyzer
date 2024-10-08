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
 - [pipx](https://github.com/pypa/pipx) *optional*

 *SLT Usage Analyzer uses chrome browser as the default option for viewing the GUI. Other browsers can be specified in the config file.*

#### Installing via `pip`

```python
pip install git+https://github.com/gamithaKalharaW/SLT-Usage-Analyzer
```
The application can be run either as a python module or as an executable script.

```python
python -m sltusageanalyzer
```
*or*
```python
sltanalyzer
```

#### Installing via `pipx`

```python
pipx install git+https://github.com/gamithaKalharaW/SLT-Usage-Analyzer
```

The application can be run as an executable script.

```python
sltanalyzer
```

#### Installing from wheel file
 - Download the wheel file from [here](https://github.com/gamithaKalharaW/SLT-Usage-Analyzer/releases/)
 - Run either `pip install` or `pipx install` to install the wheel file.

#### Packaging from source
You can also manualy build the wheel file & install it using `poetry`.

```python
git clone https://github.com/gamithaKalharaW/SLT-Usage-Analyzer
cd SLT-Usage-Analyzer
poetry build
cd dist
# pip or pipx
pip install sltusageanalyzer*.whl
```

## Configuration

The configuration file is stored at `%HOMEPATH%\.sltusageanalyzer\.analyzer.config`.

### Options
 - `BROWSER_PATH`: Path to browser. Defaults to `C:\Program Files\Google\Chrome\Application\chrome.exe`
 - Auth data(`USERNAME`, `PASSWORD`, `ID`): SLT credentials.


## Todo

 - [ ] Add cli option to update config file.
 - [ ] Update config.hash based on users custamizations.
