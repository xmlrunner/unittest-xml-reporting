# -*- coding: utf-8 -*-

"Build script."

set(
    project = 'unittest-xml-reporting',
    
    # Build output directory
    build_path = 'build',
)

def build():
    "Build the application."
    test()
    local('python setup.py sdist bdist_egg')

def skip_tests():
    "Prevent the tests from running."
    set(ignore_tests = True)

def test():
    "Run the tests."
    prepare()
    
    # Analyze the source code
    local("""export PYTHONPATH=src; pylint --include-ids=y -f parseable \
        --disable-msg="W0142,W0232,R0903,W0201,R0904,W0403,E1101" \
        xmlrunner > $(build_path)/pylint.txt""")
    
    # Ignore the tests?
    if get('ignore_tests'):
        return
    
    # Run the tests
    local('python setup.py test')

def prepare():
    "Prepare the build environment."
    clean()
    local('mkdir -p $(build_path)')

def clean():
    "Remove the build directory."
    local('rm -fR $(build_path)')
