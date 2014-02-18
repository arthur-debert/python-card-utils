##
## Distributed as part of cardutils.
##

"""
Author: Jeff Petkau

This code is in the public domain. You can run it, copy it, change
it, sell it, eat it, or claim you wrote it; I don't care.

inverse regex:
    given a regular expression string, produces random strings that
    match the expression.

    usage:
        import reinv
        print reinv.random_from_pattern("[a-z]*")
        --> gxbf

        print reinv.random_from_pattern("(cat |dog )+")
        --> cat cat dog cat

        print reinv.random_from_pattern("(cat |dog )+")
        --> dog dog


some of the many cases that this code doesn't handle well:
    (foo|x*)(^blah|stuff)

        matches blah, foostuff, xstuff, xxstuff, xxxstuff, ...

        one of the second group's cases is made impossible by what the
        first group matched.  We need to backtrack to generate correct
        results.

    ((cat|dog)\2)*

        I don't know what the semantics of this case are supposed to be;
        playing with sre.match() didn't help much.

    case insensitivity, regular expression flags, etc.

As a cheap hack to deal with being so crippled, we make repeated attempts
to generate random strings, check them with re.match(), and return the
first one that matches. This means that we'll never return an invalid
string, although we may not return all valid strings and we may be unable
to generate any strings for some legitimate expressions.
"""

import random,string,exceptions
from sre_constants import *
import sre_parse,sre

STAR_REPEAT_CHANCE = .7
MAX_RE_ATTEMPTS = 10


class FailedToGenerate(exceptions.Exception):
    pass


def nots(s):
    r = [chr(i) for i in range(256) if chr(i) not in s]
    return ''.join(r)


allchars = nots('')


category_chars = {
    CATEGORY_SPACE: string.whitespace,
    CATEGORY_NOT_SPACE: nots(string.whitespace),
    CATEGORY_DIGIT: string.digits,
    CATEGORY_NOT_DIGIT: nots(string.digits),
    CATEGORY_WORD: string.digits + string.letters + '_',
    CATEGORY_NOT_WORD: nots(string.digits + string.letters + '_'),
    CATEGORY_LINEBREAK: '\n\r',
    CATEGORY_NOT_LINEBREAK: nots('\n\r'),
}


def cons_lookup(index, groups):
    """cons_lookup(int, cons_list) -> string
    cons_list is either None, or a tuple of the form (int, string, cons_list).
    This is a handy way to keep track of group bindings we've made.
    """
    while groups is not None:
        i, v, groups = groups
        if i==index:
            return v
    raise FailedToGenerate,'group %d not matched'%i


def random_from_sub(tok,val,groups):
    """given a token and associated value (as produced by sre_parse),
    and a cons-list of group bindings, returns a string that matches
    the subpattern defined by the token/value/groups, and a new
    cons-list of group bindings.
    """

    if tok is LITERAL:
        return chr(val), groups

    if tok is ANY:
        return random.choice(allchars), groups

    if tok is AT:
        # ignore AT tokens
        return '', groups

    if tok is IN:
        t,v = random.choice(val)
        return random_from_sub(t, v, groups)

    if tok is RANGE:
        lo, hi = val
        return chr(random.randint(lo,hi)), groups

    if tok is BRANCH:
        assert val[0] is None
        return random_from_seq(random.choice(val[1]), groups)

    if tok is MAX_REPEAT or tok is MIN_REPEAT:
        lo, hi, seq = val
        r = []
        for i in range(hi):
            if i>=lo and random.random()>STAR_REPEAT_CHANCE: break
            s,groups = random_from_seq(seq,groups)
            r.append(s)

        return ''.join(r), groups

    if tok is SUBPATTERN:
        index, seq = val
        r, g = random_from_seq(seq, groups)
        if index is not None:
            g = (index, r, g)
        return r, g

    if tok is GROUPREF:
        return cons_lookup(val,groups), groups

    if tok is CATEGORY:
        return random.choice(category_chars[val]), groups

    raise NotImplementedError,'token %s not implemented yet'%tok


def random_from_seq(seq,groups):
    oseq = []
    for tok,val in seq:
        s,groups = random_from_sub(tok,val,groups)
        oseq.append(s)
    return ''.join(oseq), groups


def random_from_pattern(pattern):
    seq = sre_parse.parse(pattern)

    # Make several tries at generation before giving up.
    # Failure can be indicated by a FailedToGenerate exception,
    # or just by returning a bogus string. (The latter check
    # allows us to be a little sloppy in some of the difficult
    # cases.)
    for i in range(MAX_RE_ATTEMPTS):
        try:
            r = random_from_seq(seq,None)[0]
            if sre.match(pattern, r):
                return r
        except FailedToGenerate:
            pass

    raise FailedToGenerate


if __name__ == '__main__':
    def check(p):
        print '\nMatches for %s:' % p
        for i in range(5):
            try:
                r = random_from_pattern(p)
                assert sre.match(p,r)
            except FailedToGenerate:
                r = 'failed!'
            print '    ',r

    check('foo$foo')
    check('x')
    check('xy')
    check('x|y')
    check('x|y|z')
    check('[abc]')
    check('[a-z]')
    check('[A-Z]')
    check('cat|dog')
    check('cat|dog|mouse')
    check('c[aeiou]t|d[aeiou]g|mouse')
    check('x*')
    check('y+')
    check('(cat |dog )*')
    check('(cat |dog )(\\1)*')
    check('-?[0-9]+\.[0-9]{2}')
    check('-?\d+\.\d\d')
    check('.*foo.*')
    check('\w+( \w+)*')
    check('[A-Z][a-z]*( [a-z]+)*\\.')
    check('( [aeiouAEIOU]?([bcdfghjklmnpqrstvwxyz][aeiou]){1,4})+')
    check('(( [aeiouAEIOU]?([bcdfghjklmnpqrstvwxyz][aeiou]){1,4})\\2?)+')
    check('<[a-z<>]*>')
    check('<[a-z<>]*?>')
    check('Since (?P<big>cats|dogs) chase (?P<small>mice|squirrels|elephants), (?P=small) dislike (?P=big)\.')
