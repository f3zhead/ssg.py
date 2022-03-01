#!/usr/bin/python
# todo:
# uh redo ignore cuz globs weird
# global variables and shit
# print_status
# make pandoc do the heavy lifting cause regex sux
# change pypandoc to subprocess
# all that render_thingy stuff

import os
import glob
import re
import sys
import fnmatch
import shutil
# import subprocess
import pypandoc

USAGE = "ssg.py src dst title base_url"


def parse_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser()
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
        # remove trailing slashes, then get the real path
        return os.path.realpath(os.path.normpath(input_file), strict=True)
    except:
        print("Could not resolve path: {}".format(input_file))
        raise SystemExit

def ignore_files():
    # add files to ignore
    # note: in original ssg6 script hidden files are ignored only if there is no .ssgignore
    # first ignore hidden files, header + footer files
    ignore_files = ['*/.*', '*/_*']
    try:
        # is there more to this?
        with open(os.path.join(source_dir, '.ssgignore')) as ssgignore:
            for line in ssgignore.readlines():
                ignore_files.append('*/{}*'.format(line))
    except:
        # fail quietly
        pass
    # convert ignore_files to tuple (or should I use a set?)
    # haha im so clever
    return tuple(set(ignore_files))

def print_status():
    pass

def copy_dirs(source_dir, dest_dir):
    # ignore all files
    def _ignore_files(directory, files):
        ignored = []
        # ignore patterns that match IGNORE
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(files, pattern))
        # also ignore files
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
        # remove duplicates
        return set(files + ignored)
    # copy subdirectories of src to dst, ignore stuff
    shutil.copytree(source_dir, dest_dir, ignore=_ignore_files, dirs_exist_ok=True)

def list_subdirectories(directory):
    dir_list = []
    ignored = []
    # remove trailing slashes, just to be safe
    # or i can use os.path.split and os.path.join? i dunno
    directory = os.path.normpath(directory)
    # recursively search for files, ignore those in IGNORE and hidden files
    for root, directories, files in os.walk(directory, topdown=True):
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(directories, pattern))
        directories[:] = [d for d in directories if d not in ignored]
        for dir_name in directories:
            dir_path = os.path.join(root, filename)
            dir_list.append(filepath)
    return dir_list

def list_files(directory):
    file_list = []
    ignored = []
    # remove trailing slashes, just to be safe
    # or i can use os.path.split and os.path.join? i dunno
    ## directory = directory.rstrip("/")
    # recursively search for files, ignore those in IGNORE and hidden files
    for root, directories, files in os.walk(directory, topdown=True):
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(files, pattern))
        files[:] = [f for f in files if f not in ignored]
        # actually we need to match the pattern
        for filename in files:
            filepath = os.path.join(root, filename)
            file_list.append(filepath)
    return file_list

def list_affected_files(directory, dest_files):
    file_list = []
    has_partials = []
    last_modification = os.stat(dest_files).st_atime
    ## remove trailing slashes, just to be safe
    ## directory = directory.rstrip("/")
    # recursively search for files, ignore those in IGNORE
    for root, directories, files in os.walk(directory, topdown=True):
        # create list of files to be ignored
        for pattern in IGNORE:
            ignored.extend(fnmatch.filter(files, pattern))
            ignored.extend(fnmatch.filter(directories, pattern))
        directories[:] = [d for d in directories if d not in ignored]
        files[:] = [f for f in files if f not in ignored]
        for filename in files:
            info = filename.stat()
            if (info.st_mtime > last_modification):
                file_path = os.path.join()
                file_list.append(os)
            if filename.endswith(PARTIAL_EXTENSIONS):
               has_partials.append(filename)
    # return has_partials if has_partials is not empty
    # why tf does it matter if it's a js/css file? wtf?
    return has_partials if not has_partials else file_list

def list_pages(directory):
    # oh god regex no no no
    pages = list_files(directory)
    for page in pages:
        # should i compile into regex object?
        if page.endswith('/index.html'):
            page = re.sub("/index.html", "/", page)
        if page.endswith('.md'):
            page = re.sub(".md", ".html", page)
        if page.beginswith("./"):
            page = re.sub("^./", "", page)
    return pages


def render_html_file(body, title):
    # if the body has an <html> starting or closing tag, just spit it back
    if re.search(r"<\/?[Hh][Tt][Mm][Ll]", body):
        return body
    # look for h1 tag
    has_h1 = re.search(r"<\s*[Hh]1(>|\s[^>]*>)", body)
    if has_h1:
        t = has_h1.string[has_h1.start():has_h1.end()]
        # remove h1 closing tag
        t = re.sub(r"<\s*\/\s*[Hh]1.*", "", t, count=1)
        # remove leading and trailing whitespace
        t = re.sub(r"^\s*|\s$", "", t)
        if t:
            title = t + " &mdash; " + title
    result = ''
    header = HEADER.split(sep='\n')
    n = len(header)
    for i in range(n):
        line = header[i]
        has_title = re.search(r"<title></title>", line.lower())
        if has_title:
            head = line[0:has_title.start()]
            tail = line[has_title.start():has_title.end()]
            result = '\n'.join((result, head, ' '.join(("<title>", title, "</title>")), tail))
        else:
            result = '\n'.join((result, line))
    result = '\n'.join((result, body, FOOTER))
    return result
        # more stuff blah blah blah


def render_markup_files(files, src, dst, title):
    import json
    for f in files:
        output_path = (os.path.splitext(f)[0] + ".html").replace(src, dst, 1)
        # try:
        rendered_html = pypandoc.convert_file(source_file=f, to="html", extra_args=["--quiet", "--defaults=pandoc/defaults.yaml"])
        # skip index
        if os.path.basename(output_path) != "index.html":
            file_metadata = json.loads(pypandoc.convert_file(source_file=f, to="html", extra_args=["--quiet", "--template=pandoc/templates/metadata.ext"]))
            # convert all dictionary keys to lowercase
            file_metadata = {k.lower(): v for k, v in file_metadata.items()}
            date = file_metadata['date']
            title = file_metadata['title']
            header = "{}\n<p class=\"date\" {} </p>".format(title, date)
            complete_file = '\n'.join((header, rendered_html))
            # don't make function to render_toc
            # use pandoc yaml metadata toc option in the md files instead
            output_html = render_html_file(complete_file, title)
        else:
            # don't need date, title and toc for index.html
            # output_html = rendered_html
            output_html = render_html_file(rendered_html, title)
        with open(output_path, 'w') as output:
            output.write(output_html)
        # except RuntimeError:
        #     print("Could not render file: {}".format(f))
        #     raise SystemExit

def render_html_files(files, src, dst, title):
    for f in files:
        output_path = f.replace(src, dst, 1)
        with open(f) as html_file:
            contents = html_file.read()
        output_text = render_html_file(contents, title)
        with open(output_path, 'w') as output:
            output.write(output_text)


def render_article_list(urls, base_url, source_dir, dest_dir):
    # hehe i'll do this later
    pass

def check_deps():
    if not shutil.which("pandoc"):
        print("could not find pandoc, do you have it installed?")
        raise SystemExit


def main():
    args = parse_arguments()
    global source_dir, dest_dir
    source_dir = readlink_file(args.src)
    dest_dir = readlink_file(args.dst)
    # should this be before initialization of source_dir
    if (not os.path.isdir(source_dir)) or (not os.path.isdir(dest_dir)):
        print("No such directory")
        raise SystemExit

    global IGNORE, MARKUP_EXTENSIONS, PARTIAL_EXTENSIONS
    IGNORE = ignore_files()
    MARKUP_EXTENSIONS = ('.md', '.org')
    PARTIAL_EXTENSIONS = ('.html','.js', '.css')

    # files - wtf does this mean?
    global title, HEADER, FOOTER
    title = args.title
    HEADER = ''
    header_path = os.path.join(source_dir, '_header.html')
    try:
        with open(header_path) as header_file:
            HEADER = header_file.read()
    except:
        # fail quietly
        pass

    FOOTER = ''
    footer_path = os.path.join(source_dir, '_footer.html')
    try:
        with open(footer_path) as footer_file:
            FOOTER = footer_file.read()
    except:
        # fail quietly
        pass

    # check that pandoc is installed
    check_deps()

    copy_dirs(source_dir, dest_dir)
    # files to operate on
    files = []
    dest_file_list = os.path.join(dest_dir, '.files')
    try:
        files = list_affected_files(source_dir, dest_file_list)
    except:
        files = list_files(source_dir)

    # try:
    if files:
        with open(dest_file_list, 'w') as files_list:
            files_str = """{}""".format('\n'.join(files))
            files_list.write(files_str)
        # render all markup files
        markup_files = []
        html_files = []
        other_files = []
        for f in files:
            if f.endswith(MARKUP_EXTENSIONS):
                markup_files.append(f)
            elif f.endswith('.html'):
                html_files.append(f)
            else:
                other_files.append(f)

        render_markup_files(markup_files, source_dir, dest_dir, title)
        render_html_files(html_files, source_dir, dest_dir, title)
    # add more exceptions later
    # except:
    #     print("Could not write to {}!".format(dest_file_list))




main()
