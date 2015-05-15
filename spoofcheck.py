#! /usr/bin/env python

import sys

from colorama import init as color_init

import emailprotectionslib.dmarc as dmarclib
import emailprotectionslib.spf as spflib

from libs.PrettyOutput import output_good, output_bad, \
    output_info, output_error, output_indifferent


def check_spf_redirect_mechanisms(spf_record):
    redirect_domain = spf_record.get_redirect_domain()

    if redirect_domain is not None:
        output_info("Processing an SPF redirect domain: %s" % redirect_domain)

        return is_spf_record_strong(redirect_domain)

    else:
        return False


def check_spf_include_mechanisms(spf_record):
    include_domain_list = spf_record.get_include_domains()

    for include_domain in include_domain_list:
        output_info("Processing an SPF include domain: %s" % include_domain)

        strong_all_string = is_spf_record_strong(include_domain)

        if strong_all_string:
            return True

    return False


def check_spf_all_string(spf_record):
    strong_spf_all_string = True
    if spf_record.all_string is not None:
        if spf_record.all_string == "~all" or spf_record.all_string == "-all":
            output_indifferent("SPF record contains an All item: " + spf_record.all_string)
        else:
            output_good("SPF record All item is too weak: " + spf_record.all_string)
            strong_spf_all_string = False
    else:
        output_good("SPF record has no All string")
        strong_spf_all_string = False

    return strong_spf_all_string


def is_spf_record_strong(domain):
    strong_spf_record = True
    spf_record = spflib.SpfRecord.from_domain(domain)
    if spf_record is not None:
        output_info("Found SPF record:")
        output_info(str(spf_record.record))

        strong_all_string = check_spf_all_string(spf_record)
        if strong_all_string is False:

            redirect_strength = check_spf_redirect_mechanisms(spf_record)
            include_strength = check_spf_include_mechanisms(spf_record)

            strong_spf_record = False

            if redirect_strength is True:
                strong_spf_record = True

            if include_strength is True:
                strong_spf_record = True
        else:
            output_good(domain + " has no SPF record!")
            strong_spf_record = False

    return strong_spf_record


def get_dmarc_record(domain):
    dmarc = dmarclib.DmarcRecord.from_domain(domain)
    if dmarc is not None:
        output_info("Found DMARC record:")
        output_info(str(dmarc.record))
        return dmarc


def check_dmarc_extras(dmarc_record):
    if dmarc_record.pct is not None and dmarc_record.pct != str(100):
            output_indifferent("DMARC pct is set to " + dmarc_record.pct + "% - might be possible")

    if dmarc_record.rua is not None:
        output_indifferent("Aggregate reports will be sent: " + dmarc_record.rua)

    if dmarc_record.ruf is not None:
        output_indifferent("Forensics reports will be sent: " + dmarc_record.ruf)


def check_dmarc_policy(dmarc_record):
    policy_strength = False
    if dmarc_record.policy is not None:
        if dmarc_record.policy == "reject" or dmarc_record.policy == "quarantine":
            policy_strength = True
            output_bad("DMARC policy set to " + dmarc_record.policy)
        else:
            output_good("DMARC policy set to " + dmarc_record.policy)
    else:
        output_good("DMARC record has no Policy")

    return policy_strength


def is_dmarc_record_strong(domain):
    dmarc_record_strong = False

    dmarc = get_dmarc_record(domain)

    if dmarc is not None:

        dmarc_record_strong = check_dmarc_policy(dmarc)

        check_dmarc_extras(dmarc)
    else:
        output_good(domain + " has no DMARC record!")

    return dmarc_record_strong


if __name__ == "__main__":
    color_init()
    spoofable = False

    try:
        domain = sys.argv[1]

        spf_record_strength = is_spf_record_strong(domain)
        if spf_record_strength is False:
            spoofable = True

        dmarc_record_strength = is_dmarc_record_strong(domain)
        if dmarc_record_strength is False:
            spoofable = True

        if spoofable:
            output_good("Spoofing possible for " + domain + "!")
        else:
            output_bad("Spoofing not possible for " + domain)

    except IndexError:
        output_error("Usage: " + sys.argv[0] + " [DOMAIN]")