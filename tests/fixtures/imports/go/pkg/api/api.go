package api

import "example.com/gograph/internal/store"

func New(x interface{}) interface{} { _ = store.Open; return x }
