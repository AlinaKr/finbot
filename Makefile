export PYTHONPATH := $(PYTHONPATH):$(shell pwd)
$(info PYTHONPATH=${PYTHONPATH})

export FINBOT_SECRET_PATH := $(if $(FINBOT_SECRET_PATH),$(FINBOT_SECRET_PATH),.secure/secret.txt)
$(info FINBOT_SECRET_PATH=${FINBOT_SECRET_PATH})

export FINBOT_ACCOUNTS_PATH := $(if $(FINBOT_ACCOUNTS_PATH),$(FINBOT_ACCOUNTS_PATH),.secure/accounts)
$(info FINBOT_ACCOUNTS_PATH=${FINBOT_ACCOUNTS_PATH})

export FINBOT_DB_HOSTNAME := $(if $(FINBOT_DB_HOSTNAME),$(FINBOT_DB_HOSTNAME),127.0.0.1)
$(info FINBOT_DB_HOSTNAME=${FINBOT_DB_HOSTNAME})

export FINBOT_DB_USER := $(if $(FINBOT_DB_USER),$(FINBOT_DB_USER),finbot)
$(info FINBOT_DB_USER=${FINBOT_DB_USER})

export FINBOT_DB_PASSWORD := $(if $(FINBOT_DB_PASSWORD),$(FINBOT_DB_PASSWORD),finbot)
$(info FINBOT_DB_PASSWORD=${FINBOT_DB_PASSWORD})

export FINBOT_DB_DBNAME := $(if $(FINBOT_DB_DBNAME),$(FINBOT_DB_DBNAME),finbot)
$(info FINBOT_DB_DBNAME=${FINBOT_DB_DBNAME})

export FINBOT_DB_URL := postgresql+psycopg2://${FINBOT_DB_USER}:${FINBOT_DB_PASSWORD}@${FINBOT_DB_HOSTNAME}/${FINBOT_DB_DBNAME}
$(info FINBOT_DB_URL=${FINBOT_DB_URL})


run-finbotwsrv-dev:
	env FLASK_APP=./finbot/apps/finbotwsrv/finbotwsrv.py \
		FLASK_ENV=development \
		flask run --port 5001 -h 0.0.0.0

run-snapwsrv-dev:
	env FLASK_APP=./finbot/apps/snapwsrv/snapwsrv.py \
		FLASK_ENV=development \
		flask run --port 5000 -h 0.0.0.0

run-tester-dev:
	env python3.7 -m finbot.apps.tester.tester \
			--currency EUR \
			--dump-balances --dump-assets \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNTS_PATH} \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			${TESTER_ACCOUNTS}

run-tester:
	env python3.7 -m finbot.apps.tester.tester \
			--currency EUR \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNTS_PATH} \
			${TESTER_ACCOUNTS}

confirm-override-accounts:
	[[ ! -d .secure ]] || tools/yes_no 'This will erase existing accounts, continue?'

init-accounts: confirm-override-accounts
	mkdir -p .secure && \
	tools/crypt fernet-key > ${FINBOT_SECRET_PATH} && \
	chmod 600 ${FINBOT_SECRET_PATH} && \
	cp tools/accounts.tpl.json .accounts.tmp && \
	tools/crypt fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i .accounts.tmp > ${FINBOT_ACCOUNTS_PATH} && \
	rm .accounts.tmp && \
	chmod 600 ${FINBOT_ACCOUNTS_PATH}

show-accounts:
	tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNTS_PATH} | less

edit-accounts:
	tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNTS_PATH} > .accounts.tmp && \
	chmod 600 .accounts.tmp && \
	vim .accounts.tmp && \
	tools/crypt \
		fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i .accounts.tmp > ${FINBOT_ACCOUNTS_PATH} && \
	rm .accounts.tmp

finbotdb-build:
	tools/finbotdb build

finbotdb-destroy:
	tools/finbotdb destroy

finbotdb-rebuild:
	tools/finbotdb destroy && tools/finbotdb build

finbotdb-hydrate:
	tools/finbotdb hydrate \
		--secret ${FINBOT_SECRET_PATH} \
		--accounts ${FINBOT_ACCOUNTS_PATH}

finbotdb-psql:
	env PGPASSWORD=finbot psql -h 127.0.0.1 -U finbot -d finbot
