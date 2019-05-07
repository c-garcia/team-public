PYTHON_VERSION=3.7.2

.PHONY: install/deps daily-report clean


/usr/local/bin/pipenv:
	@brew install pipenv

/usr/local/bin/pyenv:
	@brew install pyenv

${HOME}/.pyenv/versions/${PYTHON_VERSION}/bin/python3: /usr/local/bin/pyenv
	@@CFLAGS="-I$(xcrun --show-sdk-path)/usr/include" PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install ${PYTHON_VERSION}


install/deps: /usr/local/bin/pipenv ${HOME}/.pyenv/versions/${PYTHON_VERSION}/bin/python
	pipenv install --dev --python ${PYTHON_VERSION}

daily-report:
	@pipenv run python ./daily.py

clean: /usr/local/bin/pipenv
	@pipenv --rm
