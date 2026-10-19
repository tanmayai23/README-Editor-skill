CC := gcc
VERSION=1.0

.PHONY: build test

build:
	$(CC) -o app main.c

test: build
	./app --test

install:
	cp app /usr/local/bin
