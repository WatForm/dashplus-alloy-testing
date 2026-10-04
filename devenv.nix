{ pkgs, lib, config, inputs, ... }:

let

  apalacheHash = "sha256-9ztrfiDaMElHv3vkSDJQI+MPokYLcNZhK4uUV0Oe0iE=";
  alloyJarHash = lib.fakeHash;

  # 1. Fetch the specific Apalache release zip file securely
  apalacheZip = pkgs.fetchurl {
    url = "https://github.com/apalache-mc/apalache/releases/download/v0.62.2/apalache.zip";
    hash = apalacheHash;
  };

  alloyJar = pkgs.fetchurl {
    url = "https://github.com/AlloyTools/org.alloytools.alloy/releases/tag/v6.2.0";
    hash = alloyJarHash;
  };

  # 2. Extract the archive and wrap it into a clean Nix package
  apalacheCustom = pkgs.stdenv.mkDerivation {
    pname = "apalache";
    version = "0.62.2";

    src = apalacheZip;

    # Require unzip to extract the file, and makeWrapper to configure the executable binary
    nativeBuildInputs = [ pkgs.unzip pkgs.makeWrapper ];

    # Override standard unpack phases because release zips lack typical source structures
    unpackCmd = "unzip $src";

    installPhase = ''
      # Replicate standard directory structures inside the Nix store
      mkdir -p $out/share/apalache
      mkdir -p $out/bin

      # Copy all extracted contents (lib/, bin/, etc.) into the share directory
      cp -r * $out/share/apalache/

      # Make the main shell script executable
      chmod +x $out/share/apalache/bin/apalache-mc

      # Wrap the apalache-mc script so it can explicitly find its global dependencies
      makeWrapper $out/share/apalache/bin/apalache-mc $out/bin/apalache-mc \
        --prefix PATH : ${lib.makeBinPath [ pkgs.openjdk ]} \
        --set JAVA_HOME ${pkgs.openjdk}/home
    '';
  };


in

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [ 
    pkgs.alloy5
    pkgs.alloy6
    pkgs.tlaplus18
    pkgs.openjdk25
    apalacheCustom
   ];

  # https://devenv.sh/languages/
  languages.python.enable = true;

  # https://devenv.sh/processes/
  # processes.dev.exec = "${lib.getExe pkgs.watchexec} -n -- ls -la";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  # https://devenv.sh/basics/
  enterShell = ''
    hello         # Run scripts directly
    python --version # Use packages
  '';

  # https://devenv.sh/tasks/
  tasks = {
    "project:build-jar-a2t" = {
      exec = ''
        echo "📂 Setting up alloytotla.jar"
        WORKSPACE_DIR="./build-workspace/alloytotla"
        rm -rf "$WORKSPACE_DIR"
        mkdir -p "$WORKSPACE_DIR"
        cp -r ${inputs.dashplus}/. "$WORKSPACE_DIR/"
        chmod -R +w "$WORKSPACE_DIR"
        cd "$WORKSPACE_DIR"
        chmod +x ./gradlew
        ./gradlew alloytotla --no-daemon
      '';
    };
    "project:setup-InstanceChecker" = {
      exec = ''
        WORKSPACE_DIR="./build-workspace/InstanceChecker"
        echo "done setting up Instance Checker"
      '';
    };
    "devenv:enterShell".after = [ 
      "project:build-jar-a2t"
      "project:setup-InstanceChecker"
      ];
  };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
