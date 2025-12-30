*** Settings ***
Library			 ./lib/Interceptor.py

Test Setup       Setup Proxy
Test Teardown    Shutdown Proxy


*** Keywords ***

Setup Proxy
    Setup Interceptor
    Update Master Data

Shutdown Proxy
    stop services

*** Test Cases ***

Intercept Pages
    Iterate Urls