import sys

def yn (answer):
    if answer.lower() == "yes":
        return True
    elif answer.lower() == "no":
        return False
    else:
        sys.exit('\n**ERROR**\nCheck config file. Some settings only take yes or no\n')

def likelihoodCompare(one, two):
    if one == 'UNDETECTED':
        return two
    elif one == 'UNKNOWN' and not (two == 'UNDETECTED'):
        return two
    elif one == 'VERY_UNLIKELY' and not (two == 'UNDETECTED' or two == 'UNKNOWN'):
        return two
    elif one == 'UNLIKELY' and not (two == 'UNDETECTED' or two == 'UNKNOWN' or two == 'VERY_UNLIKELY'):
        return two
    elif one == 'POSSIBLE' and not (two == 'UNDETECTED' or two == 'UNKNOWN' or two == 'VERY_UNLIKELY' or two == 'UNLIKELY'):
        return two
    elif one == 'LIKELY' and not (two == 'UNDETECTED' or two == 'UNKNOWN' or two == 'VERY_UNLIKELY' or two == 'UNLIKELY'  or two == 'POSSIBLE'):
        return two
    else:
        return one 
