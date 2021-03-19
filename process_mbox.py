#!/usr/bin/env python3
import argparse
import mailbox
import sys
import nltk
from collections import Counter

from email.header import Header, decode_header, make_header

# See
# https://docs.python.org/3/library/mailbox.html#mailbox.Mailbox
# https://stackoverflow.com/questions/7331351/python-email-header-decoding-utf-8
# https://stackoverflow.com/questions/7166922/extracting-the-body-of-an-email-from-mbox-file-decoding-it-to-plain-text-regard
# https://dev.to/fferegrino/reading-emails-with-python-4o72

def get_charsets(msg):
    charsets = set({})
    for c in msg.get_charsets():
        if c is not None:
            charsets.add(c)
    return charsets


def handle_error(errmsg, emailmsg, cs):
    print()
    print(errmsg)
    print("This error occurred while decoding with ", cs, " charset.", file=sys.stderr)
    print("These charsets were found in the one email.", get_charsets(emailmsg), file=sys.stderr)
    print("This is the subject:", emailmsg['subject'], file=sys.stderr)
    print("This is the sender:", emailmsg['From'], file=sys.stderr)


def get_body_from_message(msg):
    body = None
    # Walk through the parts of the email to find the text body.
    if msg.is_multipart():
        for part in msg.walk():

            # If part is multipart, walk through the subparts.
            if part.is_multipart():

                for subpart in part.walk():
                    if subpart.get_content_type() == 'text/plain':
                        # Get the subpart payload (i.e the message body)
                        body = subpart.get_payload(decode=True)
                        # charset = subpart.get_charset()

            # Part isn't multipart so get the email body
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
                # charset = part.get_charset()

    # If this isn't a multi-part message then get the payload (i.e the message body)
    elif msg.get_content_type() == 'text/plain':
        body = msg.get_payload(decode=True)

    # No checking done to match the charset with the correct part.
    for charset in get_charsets(msg):
        try:
            body = body.decode(charset)
            break
        except UnicodeDecodeError:
            handle_error("UnicodeDecodeError: encountered.", msg, charset)
        except AttributeError:
            handle_error("AttributeError: encountered", msg, charset)
    return body


def get_subject(subject):
    if subject is None:
        return None
    subject_parts = []
    subjects = decode_header(subject)
    for content, encoding in subjects:
        try:
            subject_parts.append(content.decode(encoding or "utf8"))
        except:
            subject_parts.append(content)

    return "".join(subject_parts)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process mbox files')
    parser.add_argument('mbox_filenames', metavar='MBOX_FILE', type=str, nargs='+',
                        help='mbox file to process')
    parser.add_argument('--offsets', action='store_true',
                        help='print mail offsets in mbox file')

    args = parser.parse_args()

    nltk.download('punkt')

    unigram_counter = Counter()
    bigram_counter = Counter()

    BEGIN_SENT = '<S>'
    END_SENT = '</S>'

    for mbox_fn in args.mbox_filenames:
        print('Process mbox file', mbox_fn)

        mbox = mailbox.mbox(mbox_fn)
        for key in mbox.keys():
            # noinspection PyBroadException
            try:
                # noinspection PyProtectedMember
                start, stop = mbox._lookup(key)
            except:
                # mbox._lookup is protected
                start = None
                stop = None
            message = mbox.get(key)
            subject_header = get_subject(message['subject'])  # Could possibly be None.

            msgid = message['Message-ID']
            print('Mail %s Message-ID %s Subject %s' % (key, msgid, subject_header))
            if args.offsets and start is not None and stop is not None:
                print('Mail %s Start Offset %i Stop Offset %i' % (key, start, stop))

            body = get_body_from_message(message)

            if isinstance(body, bytes):
                for codec in ('utf-8', 'ascii', 'latin-1'):
                    try:
                        body = body.decode(codec)
                        break
                    except UnicodeDecodeError:
                        pass
            #print(body)

            sentences = nltk.tokenize.sent_tokenize(body)
            for sentence in sentences:
                tokens = nltk.wordpunct_tokenize(sentence)
                # lower tokens
                tokens = [token.lower() for token in tokens]
                unigram_counter.update(tokens)
                # Tokens with sentence marks
                sent_tokens = [BEGIN_SENT] + tokens + [END_SENT]
                bigram_counter.update(nltk.bigrams(sent_tokens))


            if message.get_content_maintype() == 'multipart':
                for part in message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    filename = part.get_filename()
                    print("Mail %s Filename %s" % (key, filename))

    output_fn = 'unigrams.tsv'
    print('Output unigrams to file', output_fn, '...')
    with open(output_fn, 'wt') as f:
        for key, value in unigram_counter.items():
            print('{}\t{:d}'.format(key, value), file=f)
    print('Done')

    output_fn = 'bigrams.tsv'
    print('Output bigrams to file', output_fn, '...')
    with open(output_fn, 'wt') as f:
        for key, value in bigram_counter.items():
            print('{}\t{:d}'.format(' '.join(key), value), file=f)
    print('Done')
