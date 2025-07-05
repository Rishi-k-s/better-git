import subprocess


def check_for_git_installation() -> str:
    result = subprocess.run(["which git"], shell=True, capture_output=True, text=True)
    print(result.stdout)
    if(result.stdout!= ""):
        print(f"found git at {result.stdout}")
        return result.stdout
    else:
        return ""


if (__name__ == "__main__"):
    check_for_git_installation() 