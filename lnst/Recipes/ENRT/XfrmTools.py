from lnst.Common.LnstError import LnstError

def generate_key(length):
    """
    Method generates key suitable for the IPsec.

    :param length: Desired length of the generated key
    :return: key
    """
    key = "0x"
    key = key + (length//8) * "0b"
    return key

def configure_ipsec_esp_aead(m1, ip1, m2, ip2, algo, algo_key, icv_len,
                             ipsec_mode, spi_vals):
    """
    This method creates states and policies for the ESP AEAD IPsec
    between two endpoinsts according to the specified parameters. The iproute2's
    ip-xfrm is used for the configuration.


    :param m1: Handle for the Host API for the endpoint
    :param ip1: IPv4 and IPv6 addresses of given device under test
    :param m2: Handle for the Host API for the other endpoint
    :param ip2: IPv4 and IPv6 addresses of other side of the endpoint
    :param algo: Encryption algorithm that will be used for the configuration of ESP
    :param algo_key: Generated key for the encryption algorithm
    :param icv_len: Length of ICV for the AEAD encryption protocol
    :param ipsec_mode: Mode of the ESP
    :param spi_vals: SPI value for the identification
    """
    for m, in1, in2,  in [(m1, ip2, ip1), (m2, ip1, ip2)]:
        m.run("ip xfrm policy flush")
        m.run("ip xfrm state flush")

        m.run("ip xfrm state add src %s dst %s proto esp spi %s "\
              "aead '%s' %s %s mode %s "\
              "sel src %s dst %s"\
              % (ip2, ip1, spi_vals[1],
                 algo, algo_key, icv_len, ipsec_mode,
                 ip2, ip1))

        m.run("ip xfrm policy add src %s dst %s dir in tmpl "\
              "src %s dst %s proto esp mode %s action allow"\
              % (in1, in2,
                 in1, in2, ipsec_mode))

        m.run("ip xfrm state add src %s dst %s proto esp spi %s "\
              "aead '%s' %s %s mode %s "\
              "sel src %s dst %s"\
              % (ip1, ip2, spi_vals[0],
                 algo, algo_key, icv_len, ipsec_mode,
                 ip1, ip2))

        m.run("ip xfrm policy add src %s dst %s dir out tmpl "\
              "src %s dst %s proto esp mode %s action allow"\
              % (in2, in1,
                 in2, in1, ipsec_mode))

def configure_ipsec_esp_ah_comp(m1, ip1, m2, ip2, ciph_alg, ciph_key, hash_alg,
                                hash_key, ipsec_mode, spi_vals):
    """
    This method creates states and policies for the ESP AH IPsec with IPcomp
    between two endpoinsts according to the specified parameters. The iproute2's
    ip-xfrm is used for the configuration.

    :param m1: Handle for the Host API for the endpoint
    :param ip1: IPv4 and IPv6 addresses of given device under test
    :param m2: Handle for the Host API for the other endpoint
    :param ip2: IPv4 and IPv6 addresses of other side of the endpoint
    :param ciph_alg: Encryption algorithm that will be used for the configuration of ESP
    :param ciph_key: Generated key for the encryption algorithm
    :param hash_alg: Algorithm for AH part of IPsec
    :param hash_key: Generated key for the authentication protocol
    :param icv_len: Length of ICV for the AH encryption protocol
    :param ipsec_mode: Mode of the ESP
    :param spi_vals: SPI value for the identification
    """
    m_keys = []
    for m in [m1, m2]:
        res = m.run("rpm -qa iproute")
        if (res.stdout.find("iproute-2") != -1):
            m_keys.append("0x")
        else:
            m_keys.append("")

    m1_key, m2_key = m_keys

    for m, d1, d2, m_key in [(m1, "out", "in", m1_key),
                             (m2, "in", "out", m2_key)]:
        m.run("ip xfrm policy flush")
        m.run("ip xfrm state flush")

        m.run("ip xfrm policy add src %s dst %s dir %s "\
              "tmpl src %s dst %s proto comp spi %s mode %s %s "\
              "tmpl src %s dst %s proto esp spi %s mode %s "\
              "tmpl src %s dst %s proto ah spi %s mode %s"
              % (ip1, ip2, d1,
                 ip1, ip2, spi_vals[3], ipsec_mode, "level use" if d1 == "in" else '',
                 ip1, ip2, spi_vals[1], ipsec_mode,
                 ip1, ip2, spi_vals[2], ipsec_mode))

        m.run("ip xfrm policy add src %s dst %s dir %s "\
              "tmpl src %s dst %s proto comp spi %s mode %s %s "\
              "tmpl src %s dst %s proto esp spi %s mode %s "\
              "tmpl src %s dst %s proto ah spi %s mode %s"
              % (ip2, ip1, d2,
                 ip2, ip1, spi_vals[0], ipsec_mode, "level use" if d2 == "in" else '',
                 ip2, ip1, spi_vals[1], ipsec_mode,
                 ip2, ip1, spi_vals[2], ipsec_mode))

        m.run("ip xfrm state add "\
              "src %s dst %s proto comp spi %s mode %s "\
              "comp deflate %s"\
              % (ip1, ip2, spi_vals[3], ipsec_mode, m_key))

        m.run("ip xfrm state add "\
              "src %s dst %s proto comp spi %s mode %s "\
              "comp deflate %s"\
              % (ip2, ip1, spi_vals[0], ipsec_mode, m_key))

        m.run("ip xfrm state add "\
              "src %s dst %s proto esp spi %s mode %s "\
              "enc '%s' %s"\
              % (ip1, ip2, spi_vals[1], ipsec_mode,
                 ciph_alg, ciph_key))

        m.run("ip xfrm state add "\
              "src %s dst %s proto esp spi %s mode %s "\
              "enc '%s' %s"\
              % (ip2, ip1, spi_vals[1], ipsec_mode,
                 ciph_alg, ciph_key))

        m.run("ip xfrm state add "\
              "src %s dst %s proto ah spi %s mode %s "\
              "auth '%s' %s"
              % (ip1, ip2, spi_vals[2], ipsec_mode,
                 hash_alg, hash_key))

        m.run("ip xfrm state add "\
              "src %s dst %s proto ah spi %s mode %s "\
              "auth '%s' %s"
              % (ip2, ip1, spi_vals[2], ipsec_mode,
                 hash_alg, hash_key))
