{
  nixConfig = {
    # Adapted From: https://github.com/divnix/digga/blob/main/examples/devos/flake.nix#L4
    accept-flake-config = true;
    auto-optimise-store = true;
    builders-use-substitutes = true;
    cores = 0;
    extra-experimental-features =
      "nix-command flakes impure-derivations recursive-nix";
    fallback = true;
    flake-registry =
      "https://raw.githubusercontent.com/syvlorg/flake-registry/master/flake-registry.json";
    keep-derivations = true;
    keep-outputs = true;
    max-free = 1073741824;
    min-free = 262144000;
    show-trace = true;
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "nickel.cachix.org-1:ABoCOGpTJbAum7U6c+04VbjvLxG9f0gJP5kYihRRdQs="
      "sylvorg.cachix.org-1:xd1jb7cDkzX+D+Wqt6TemzkJH9u9esXEFu1yaR9p8H8="
    ];
    trusted-substituters = [
      "https://cache.nixos.org/"
      "https://nix-community.cachix.org"
      "https://nickel.cachix.org"
      "https://sylvorg.cachix.org"
    ];
    warn-dirty = false;
  };
  description = "Manage your links!";
  inputs = rec {
    bundle = {
      url = "https://github.com/sylvorg/bundle.git";
      type = "git";
      submodules = true;
    };
    valiant.follows = "bundle/valiant";
    nixpkgs.follows = "bundle/nixpkgs";

    pyPkg-oreo.url =
      "git+https://github.com/syvlorg/oreo.git";

    flake-utils.url = "github:numtide/flake-utils";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };

    favicon = {
      url = "github:scottwernervt/favicon";
      flake = false;
    };
    urltitle = {
      url = "github:impredicative/urltitle";
      flake = false;
    };
  };
  outputs = inputs@{ self, flake-utils, ... }:
    with builtins;
    with inputs.bundle.lib;
    with flake-utils.lib;
    inputs.bundle.mkOutputs.python {
      inherit inputs self;
      pname = "falinks";
      overlayset.official.python.null = [ "inflect" "pikepdf" "requests-mock" ];
      callPackageset.python = iron.mapPassName {
        urltitle = pname:
          { buildPythonPackage, cachetools, pikepdf, beautifulsoup4, humanize }:
          buildPythonPackage rec {
            inherit pname;
            version = iron.pyVersion src;
            src = inputs.${pname};
            doCheck = false;
            propagatedBuildInputs =
              [ cachetools pikepdf beautifulsoup4 humanize ];
            pythonImportsCheck = [ pname ];
            postPatch = ''
              substituteInPlace setup.py --replace "version=cast(Match, re.fullmatch(r\"refs/tags/v?(?P<ver>\S+)\", os.environ[\"GITHUB_REF\"]))[\"ver\"]," ""
            '';
            meta = {
              description =
                "Get the page title or header-based description for a URL";
              homepage = "https://github.com/${Inputs.${pname}.owner}/${pname}";
              license = licenses.agpl3Only;
            };
          };
        favicon = pname:
          { buildPythonPackage, beautifulsoup4, requests, requests-mock
          , pytestCheckHook }:
          buildPythonPackage rec {
            inherit pname;
            version = iron.pyVersion src;
            src = inputs.${pname};
            propagatedBuildInputs = [ beautifulsoup4 requests ];
            pythonImportsCheck = [ pname ];
            checkInputs = [ pytestCheckHook requests-mock ];
            postPatch = ''
              substituteInPlace setup.py --replace "'pytest-runner'," ""
            '';
            meta = {
              description = "Find a website's favicon.";
              homepage = "https://github.com/${Inputs.${pname}.owner}/${pname}";
              license = licenses.mit;
            };
          };
      };
      callPackage = { callPackage, beautifulsoup4, favicon, inflect
        , pathvalidate, requests, urltitle }:
        callPackage (iron.mkPythonPackage {
          inherit self inputs;
          package = rec {
            src = ./.;
            postPatch = ''
              substituteInPlace pyproject.toml \
                --replace "oreo = { git = \"https://github.com/syvlorg/oreo.git\", branch = \"main\" }" ""
              substituteInPlace setup.py \
                --replace "'oreo @ git+https://github.com/syvlorg/oreo.git@main'," "" || :
            '';
            propagatedBuildInputs =
              [ beautifulsoup4 favicon inflect pathvalidate requests urltitle ];
            meta.description = "Manage your links!";
          };
        }) { };
    } { isApp = true; };
}
