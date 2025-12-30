BMO Tagging Robot Script
===========================================

Documentation
-------------

Developer Thusjanthan Kubendranathan <info@thusjanthan.com>

Discovery Phase
Keyword: Update Master Data                 <master_file (optional)>
    Iterates through the master file and defining the urls, request urls and its associated data.
    This function can be called multiple times where it will keep appending the extra details to the master
    data structure. The only caveat is that the first column (id) must be distinct.

Developer Notes
---------------

To install requirements
    pip install -r requirements/base.txt

To run tests:
    nosetests --tests lib/tests/ --with-coverage --cover-package=lib

To run flake:
    flake8

To Debug
    There is a function called: _set_trace. If you go to the line which you think is causing the issue, and type in:
        self._set_trace()
    This will intercept the call at that point using Pdb (Python Debugger), using this you can inspect, traverse the
    code to determine what is causing the issue. I generally put this command at the top of the function such as:
    handle_apply_click or traverse_card and traverse through the code to see what exactly is causing the issue.

Running The Scripts
-------------------

To Run the Robot Script
    robot intercept_bmo_pages.robot

By Default, when running the script again, only the failed
To Re-Run ONLY Failed tests, run the following command. Please note that ROW_ID takes precedence over this param
    robot --variable Rerun_failed:True intercept_bmo_pages.robot


Master Template File
--------------------

You can pass any number of master file to the update_master_data function and it would keep appending to the
master_data traversal.
