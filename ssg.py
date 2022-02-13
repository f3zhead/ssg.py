# todo:
# list_affected_files

import os
import glob
import sys
import fnmatch
import pypandoc
USAGE = "ssg.py src dst title base_url"


def parse_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser ()
    parser.add_argument('src',
            help='Source directory')
    parser.add_argument('dst',
            help='Destination directory')
    parser.add_argument('title',
            help='Website title')
    parser.add_argument('base_url',
            help='Base url of your website')
    args = parser.parse_args()
    return args

def readlink_file(input_file):
    try:
        return os.path.realpath(input_file, strict=True)
    except:
        print("Could not resolve path: {}".format(input_file))
    raise SystemExit

def ignore_files():
    # add files to ignore
    # note: in original ssg6 script hidden files are ignored only if there is no .ssgignore
    # first ignore hidden files
    ignore_files = ['.*', '_*']
    try:
        # is there more to this?
        with open(os.path.join(source_dir, '.ssgignore')) as ssgignore:
            ignore_files += ssgignore.readlines()
    except:
        # fail quietly
        pass
    # convert ignore_files to tuple
    return tuple(ignore_files)

def list_subdirectories(directory):
    # remove trailing slashes, just to be safe
    # or i can use os.path.split and os.path.join? i dunno
    directory = directory.rstrip("/")
    # recursively search for files, ignore those in IGNORE and hidden files
    # haha i love you stack overflow
    for root, directories, files in os.walk(directory, topdown=True):
        directories[:] = [d for d in directories if d not in IGNORE]
        files[:] = [f for f in files if f not in IGNORE]
        # actually we need to match the pattern
        for filename in files:
            filepath = os.path.join(root, filename)
            file_list.append(filepath)
    return file_list

def pandoc_render_files(files):
    import json
    for f in files:
        output_file = os.path.splitext(os.path.basename(f)) + ".html"
        output_path = os.path.join(dest_dir, output_file)
        try:
            rendered_html = pypandoc.convert_file(source_file=f, to="html")
            # skip index
            if output_file != "index.html":
                file_metadata = json.loads(pypandoc.convert_file(source_file=f, to="html", extra_args=["--template=pandoc/templates/metadata.ext"]))
                date = file_metadata['date']
                title = file_metadata['title']
                header = "{}\n<p class=\"date\"{}</p>".format(title, date)
                complete_file = header + rendered_html
            else:
                complete_file = rendered_html
            with open(output_path, 'w') as output:
                output.write(complete_file)
        except RuntimeError:
            print("Could not render file: {}".format(f))
            raise SystemExit

def check_deps():
    try:
        pypandoc.get_pandoc_path()
    except OSError:
        print("could not find pandoc, do you have it installed?")
        raise SystemExit

def list_affected_files(source_dir, dest_file_list):
    files = list_subdirectories()

def main():
    args = parse_arguments()
    source_dir = readlink_file(args.src)
    dest_dir = readlink_file(args.dst)
    # should this be before initialization of source_dir
    if (not os.path.isdir(source_dir)) or (not os.path.isdir(dest_dir)):
      print("No such directory")
      raise SystemExit

    IGNORE = ignore_files()
    EXTENSIONS = ('.md', '.html','.org')
    # files - wtf does this mean?
    title = args.title
    header = ''
    header_path = os.path.join(source_dir, '_header.html')
    try:
            with open(header_path) as header_file:
                header = header_file.read()
    except:
        # fail quietly
        pass

    footer = ''
    footer_path = os.path.join(source_dir, '_footer.html')
    try:
            with open(footer_path) as footer_file:
                footer = footer_file.read()
    except:
        # fail quietly
        pass

    # check that pandoc is installed
    check_deps()

    from shutil import copytree, ignore_patterns
    # copy subdirectories of src to dst
    copytree(source_dir, dest_dir, ignore=ignore_patterns(IGNORE))

    files = ''
    try:
        dest_file_list = os.path.join(dest_dir, '.files')
        files = list_affected_files(source_dir, dest_file_list)
    except:
        # something going on here, i forgot waht
        pass

main()
