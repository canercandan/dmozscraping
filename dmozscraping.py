#!/usr/bin/env python3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Caner Candan <caner@candan.fr>, http://caner.candan.fr
#

import argparse, logging, sys
from collections import OrderedDict

from lxml import etree
import sys
from urllib.parse import urlparse
import rank_provider as rp

providers = (rp.AlexaTrafficRank(), rp.GooglePageRank(),)

def scrap(args):
    logger = logging.getLogger("scrap")

    def fast_iter(context, func):
        for event, elem in context:
            func(elem)
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        del context

    with open(args.result_file, 'w') as r:
        __set = set()

        def prettyprint(elem):
            link = elem.attrib.get(args.attribute_name, '')
            o = urlparse(link)
            if o.netloc in __set: return

            __set.add(o.netloc)
            r.write('%s%c %s%c ' % (o.netloc, args.separator, link,
                                    args.separator))

            for child in elem.getchildren():
                r.write('%s%c ' % (child.text.encode() if child.text else '',
                                   args.separator))

            r.write('\n')

        try:
            context = etree.iterparse(args.content_file, tag=args.tag)
            fast_iter(context, prettyprint)
        except FileNotFoundError as e:
            logger.error('content file (%s) not found.' % args.content_file)

def rank(args):
    logger = logging.getLogger("rank")

    with open(args.result_file, 'w') as r:
        with open(args.content_file, 'r') as c:
            for line in c:
                netloc = line.split(args.separator)[0]

                for p in providers:
                    r.write('%s%c %d%c\n' % (netloc, args.separator,
                                             p.get_rank(netloc) or 0,
                                             args.separator))
                    r.flush()

def shot(args):
    logger = logging.getLogger("shot")

if __name__ == '__main__':
    logger = logging.getLogger("main")
    common_options = {'formatter_class': argparse.ArgumentDefaultsHelpFormatter}
    parser = argparse.ArgumentParser(description='dmoz scrapping program.', **common_options)

    levels = OrderedDict([('debug', logging.DEBUG),
                          ('info', logging.INFO),
                          ('warning', logging.WARNING),
                          ('error', logging.ERROR),
                          ('quiet', logging.CRITICAL),])

    parser.add_argument('--verbose', '-v', choices=[x for x in levels.keys()], default='error', help='set a verbosity level')
    parser.add_argument('--levels', '-l', action='store_true', default=False, help='list all the verbosity levels')
    parser.add_argument('--output', '-o', help='all the logging messages are redirected to the specified filename.')
    parser.add_argument('--debug', '-d', action='store_const', const='debug', dest='verbose', help='Display all the messages.')
    parser.add_argument('--info', '-i', action='store_const', const='info', dest='verbose', help='Display the info messages.')
    parser.add_argument('--warning', '-w', action='store_const', const='warning', dest='verbose', help='Only display the warning and error messages.')
    parser.add_argument('--error', '-e', action='store_const', const='error', dest='verbose', help='Only display the error messages')
    parser.add_argument('--quiet', '-q', action='store_const', const='quiet', dest='verbose', help='Quiet level of verbosity only displaying the critical error messages.')

    subparsers = parser.add_subparsers(help='sub-command help')

    sp = subparsers.add_parser('scrap', help='Scrap content file', **common_options)
    sp.add_argument('--content_file', '-c', help='Path to the content file', default='content.rdf.u8')
    sp.add_argument('--result_file', '-r', help='Path to the resulting file (csv)', default='websites.csv')
    sp.add_argument('--interactive', '-i', help='interactive mode', action='store_true', default=False)
    sp.add_argument('--tag', '-T', help='tag used as pattern to select content', default='{http://dmoz.org/rdf/}ExternalPage')
    sp.add_argument('--attribute_name', help='attribute name used to identify links', default='about')
    sp.set_defaults(func=scrap)

    sp = subparsers.add_parser('rank', help='Compute alex and page ranks', **common_options)
    sp.add_argument('--content_file', '-c', help='Path to the websites file (csv)', default='websites.csv')
    sp.add_argument('--result_file', '-r', help='Path to the result file (csv)', default='ranking.csv')
    sp.set_defaults(func=rank)

    sp = subparsers.add_parser('shot', help='Screenshot websites', **common_options)
    sp.add_argument('--content_file', '-c', help='Path to the websites file (csv)', default='websites.csv')
    sp.add_argument('--directory', '-D', help='Path to a directory where images will be saved', default='screenshots')
    sp.set_defaults(func=shot)

    parser.add_argument('--separator', '-S', help='Separator used for csv file.', default=';')

    args = parser.parse_args()

    if args.levels:
        print("Here's the verbose levels available:")
        for keys in levels.keys():
            print("\t", keys)
        sys.exit()

    if (args.output):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            filename=args.output, filemode='a'
            )
    else:
        logging.basicConfig(
            level=levels.get(args.verbose, logging.NOTSET),
            format='%(name)-12s: %(levelname)-8s %(message)s'
        )

    if 'func' not in args:
        parser.print_help()
        sys.exit()

    args.func(args)
