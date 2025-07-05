import os
from  requirement_files_for_git import check_for_git_installation


def main():
    check_for_git_installation()
    get_logseq_path = input("Enter LogSeq Path : ")
    update_page_name = "syncall.md"
    file_path_logseq = os.path.join(get_logseq_path, update_page_name)

    with open(file_path_logseq, "w") as the_update_page:
        the_update_page.write("## Yay, succesfully prepared the logseq git sync files\n")
    


if __name__ == "__main__":
    main()
