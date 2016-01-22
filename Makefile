
build/publish/bin:
	virtualenv build/publish
	build/publish/bin/pip install wheel twine

checkversion:
	git log -1 --oneline | grep -q "Bump version" || (echo "DID NOT DO VERSION BUMP"; exit 1)
	git show-ref --tags | grep -q $$(git log -1 --pretty=%H) || (echo "DID NOT TAG VERSION"; exit 1)

dist: checkversion build/publish/bin
	build/publish/bin/python setup.py sdist
	build/publish/bin/python setup.py bdist_wheel

publish: dist/ build/publish/bin
	build/publish/bin/twine upload dist/*

clean:
	rm -rf build/ dist/

.PHONY: checkversion dist publish clean
