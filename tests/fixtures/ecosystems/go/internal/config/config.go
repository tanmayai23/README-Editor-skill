package config

import "os"

func Load() string { return os.Getenv("GOTOOL_HOME") }
