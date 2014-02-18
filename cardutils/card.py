##
## Cardutils
## Copyright (c) Henry Bucklow 2005
##
## This file is part of Cardutils.
##
## Cardutils is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## Cardutils is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Cardutils; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##

import lxml.etree
import re
import random
import os.path
import sys

import reinv

class Card:
    """
    This object represents a card. It contains the variables
        number - the card number
        industry - the industry the card issuer is associated with
        issuer - the card issuer - None if unknown
    """

    number = None
    industry = None
    issuer = None

    def __str__(self):
        if self.issuer is None:
            issuer = "Unknown"
        else:
            issuer = self.issuer
            
        return "<Card Number=%s, Industry=\"%s\", Issuer=\"%s\">" % \
                                        (self.number, self.industry, issuer)

ccinfo = os.path.join(sys.prefix, "share")
ccinfo = os.path.join(ccinfo, "cardutils")
ccinfo = os.path.join(ccinfo, "cardData.xml")

number = re.compile("^((([0-9])[0-9]{5})([0-9]{1,12}))([0-9])$")

def canonicalForm(string):
    # Delete spaces from the string
    return string.replace(" ", "")

def check(string):
    """
    Checks the card number for obvious problems. Checks for well-
    formedness, and checks if the checksum digit (last digit)
    is correct for the number.
    """

    string = canonicalForm(string)

    match = number.match(string)
    if match is None:
        return False

    nochecksum = match.group(1)
    checksum = match.group(5)

    check = checkLuhn(int(nochecksum), int(checksum))
    if check is False:
        return False

    return True

def matchesLength(lengthstring, length):
    ranges = lengthstring.split(",")
    for range in ranges:
        if re.match("^[0-9]+-[0-9]+$", range) is not None:
            min, max = range.split("-")
            if length >= int(min) or length <= int(max):
                return True
        else:
            if length == int(range):
                return True

    return False

def randomLength(lengthstring):
    ranges = lengthstring.split(",")
    range = random.choice(ranges)
    if re.match("^[0-9]+-[0-9]+$", range) is not None:
        min, max = range.split("-")
        return random.randint(int(min), int(max))
    else:
        return int(range)

def analyse(string):
    """
    Analyses a card, and returns a new Card object based on the string given.
    The analysis consists of checking the card (see the check function) and
    looking up to see if it matches any of the known issuers.
    """

    string = canonicalForm(string)
    
    if check(string) is False:
        raise Exception, "Card number %s is not well-formed." % string

    match = number.match(string)
    
    mii = match.group(3)
    issuer = match.group(2)
    account = match.group(4)
    nochecksum = match.group(1)
    checksum = match.group(5)

    card = Card()
    card.number = string

    doc = lxml.etree.parse(ccinfo)
    result = doc.xpath("/cardData/miis/mii[@value=%s]" % mii)[0]
    card.industry = result.text

    issuers = doc.xpath("//issuer")
    for possibleIssuer in issuers:
        matches = possibleIssuer.xpath("match")
        name = possibleIssuer.find("name").text
        
        for match in matches:
            length = match.attrib["length"]
            regex = "^" + match.text + "$"

            if matchesLength(length, len(string)) and re.match(regex, issuer) is not None:
                card.issuer = name
                break

        if card.issuer is not None:
            break

    return card

def number2digits(number):
    """
    Converts a number to a list of its digits (base 10).
    """

    string = str(number)
    digits = []
    for c in string:
        digits.append(int(c))

    return digits

def digits2number(digits):
    """
    Converts a digit list to a number.
    """

    number = 0
    for i, digit in enumerate(digits):
        number += (10**i) * digit

    return number

def luhn(number):
    """
    Computes and returns the Luhn checksum of the given
    number.
    """

    digits = number2digits(number)

    digits.reverse()
    sum = 0
    for i, digit in enumerate(digits):
        if i % 2 == 0:
            temp = digit * 2
            if temp > 9:
                temp -= 9
            sum += temp
        else:
            sum += digit

    return (10 - (sum % 10)) % 10

def checkLuhn(number, checksum):
    """
    Checks whether the Luhn checksum of the number is correct.
    """

    cs = luhn(number)
    if checksum == cs:
        return True
    else:
        return False

def randomCard(types=["credit", "debit"]):
    """
    Generates a "valid" (i.e. belongs to a valid issuer, and has a
    correct checksum digit) random credit card number. Returns a 
    Card object.

    Types is a list of card type strings from cardData.xml. The default
    is ["credit", "debit"] which means a random credit or debit card
    number is returned. This is probably what you want.
    """

    doc = lxml.etree.parse(ccinfo)
    issuers = doc.xpath("//issuer")
    random.shuffle(issuers)
    length = 0
    issuerId = None
    
    for issuer in issuers:
        if types == []:
            correctType = True
        else:
            correctType = False

        for type in types:
            if issuer.xpath("preceding-sibling::type")[0].text == type:
                correctType = True

        if correctType:
            matches = issuer.xpath("match")
            match = random.choice(matches)
            length = randomLength(match.attrib["length"])
            issuerId = reinv.random_from_pattern("^" + match.text + "$")
            break

    if issuerId is None:
        raise Exception, "Unknown card type."

    cardNum = issuerId
    for i in range(7, length):
        cardNum += str(random.randint(0, 9))
        
    cardNum += str(luhn(int(cardNum)))

    card = analyse(cardNum)
    return card
