package main

import (
	"fmt"

	"example.com/gograph/internal/store"
	"example.com/gograph/pkg/api"
)

func main() { fmt.Println(api.New(store.Open())) }
