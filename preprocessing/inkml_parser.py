'''Parses the inkml files of the dataset into workable hierarchical objects'''
import sys

def load(filename):
    with open(filename, 'r') as f:
        return f.read()


def strip(enclosed_string: str):
    '''Returns the string with brackets or quotation marks removed from both ends'''
    return enclosed_string.strip("</>'\"")


def tag_type(tag):
    '''Returns the type of the tag'''
    return strip(tag).split()[0]


def find_open_tag(inkml: str, start_idx: int) -> tuple:
    '''Finds the next opening tag and returns the indexes of the brackets.
    Returns tuple of negative integers upon exceptions.
    '''
    if len(inkml) <= start_idx:
        return -1, -1
    if inkml[start_idx] != '<':
        return -2, -2

    head = start_idx

    while head < len(inkml) and inkml[head] != '>':
        head += 1

    if head == len(inkml):  # closing bracket not found
        return -3, -3
    else:
        end_idx = head
        return start_idx, end_idx


def find_close_tag(open_tag, inkml, start_idx) -> tuple:
    '''Searches for and returns the indexes of the corresponding close_tag's brackets for the specified open_tag'''
    if len(inkml) <= start_idx:
        return -1, -1

    close_tag = open_tag_to_close_tag(open_tag)
    to_close = 1
    parsing_tag = False
    tag_open = 0
    tag_close = 0
    head = start_idx
    while head < len(inkml):
        if not parsing_tag:
            if inkml[head] == '<':  # tag started
                parsing_tag = True
                tag_open = head
        else:
            if inkml[head] == '>':  # tag ended
                parsing_tag = False
                tag_close = head
                tag = inkml[tag_open: tag_close + 1]
                if tag.startswith('</'):  # a closing tag
                    if tag == close_tag:
                        to_close -= 1
                        if to_close == 0:
                            return tag_open, tag_close
                elif tag.endswith('/>'):  # a self-closing tag
                    pass
                else:  # an opening tag
                    if tag_type(tag) == tag_type(open_tag):
                        to_close += 1
        head += 1
    return -2, -2
        

def open_tag_to_close_tag(open_tag):
    '''Returns the closing tag for a opening tag'''
    return '</' + tag_type(open_tag) + '>'


class TagSpace:
    '''Parses an inkml file to create a hierarchical tree-like structure of tags and data'''
    def __init__(self, inkml: str):
        inkml = inkml.replace('\r', '')
        inkml = inkml.replace('\n', '')
        inkml = inkml.replace('\t', '')
        inkml = inkml.replace(' ' * 4, '')

        self.inkml = inkml
        self.tagspaces = []
        self.data = None

        open_tag_start, open_tag_end = find_open_tag(inkml, 0)
        assert open_tag_start >= 0

        self.open_tag = inkml[open_tag_start: open_tag_end + 1]

        if self.open_tag[-2] == '/':  # the tag closes itself
            self.close_tag = self.open_tag

        else:  # There is a separate close tag
            self.close_tag = open_tag_to_close_tag(self.open_tag)
            assert inkml.endswith(self.close_tag)
            # strip the opening and closing tags
            inkml = inkml[len(self.open_tag):-len(self.close_tag)]

            # if there are no sub-tagspaces, this tagspace must contain data
            if inkml[0] != '<':
                self.data = inkml
            # else, this tagspace must contain sub-tagspaces
            else:
                head = 0
                while head < len(inkml):
                    open_tag_start, open_tag_end = find_open_tag(inkml, head)
                    open_tag = inkml[open_tag_start: open_tag_end + 1]
                    assert open_tag_start >= 0

                    head = open_tag_end + 1

                    if open_tag[-2] == '/':  # the tag closes itself
                        close_tag = open_tag
                        close_tag_start, close_tag_end = open_tag_start, open_tag_end

                    else:  # There is a separate close tag
                        close_tag_start, close_tag_end = find_close_tag(open_tag, inkml, head)
                        close_tag = inkml[close_tag_start: close_tag_end + 1]
                        assert close_tag_start >= 0

                    self.tagspaces.append(TagSpace(inkml[open_tag_start: close_tag_end + 1]))
                    head = close_tag_end + 1
    
    def data_repr(self):
        threshold = 30
        if self.data is None:
            return ''
        else:
            if len(self.data) > threshold:
                return self.data[:threshold] + ' [...]'
            else:
                return self.data

    def __str__(self):
        representation = [self.open_tag]
        if self.data is not None:
            representation[0] += ': ' + self.data_repr()

        for tagspace in self.tagspaces:
            tagspace_repr = '    ' + tagspace.open_tag

            if tagspace.data is not None:
                tagspace_repr += ': ' + tagspace.data_repr()

            representation.append(tagspace_repr)
        return '\n'.join(representation)

    def __repr__(self):
        representation = [self.open_tag]
        if self.data is not None:
            representation[0] += ': ' + self.data_repr()

        for tagspace in self.tagspaces:
            for line in repr(tagspace).split('\n'):
                representation.append(' ' * 4 + line)

        representation.append(self.close_tag)
        return '\n'.join(representation)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        inkml = load(filename)
        ts = TagSpace(inkml)
        print(ts)
        print()
        print(repr(ts))

