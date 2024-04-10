{ pkgs }: {
	deps = [
		pkgs.python3
		pkgs.python3Packages.paramiko
		pkgs.python3Packages.python-dotenv
		pkgs.python3Packages.loguru
		pkgs.python3Packages.tqdm
		pkgs.python3Packages.bcrypt  # Add bcrypt here
	];
}
