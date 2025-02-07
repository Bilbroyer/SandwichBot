import configparser


def read_cache(section, option, filepath):
    """
    读取本地缓存
    :param section: str: 缓存的板块
    :param option: str: 缓存的名称
    :param filepath: str: 文件路径
    :return: str: 返回读取到的内容
    """
    # Create a new configuration object
    config = configparser.ConfigParser()
    # Read the configuration file from disk
    config.read(filepath + '.ini')
    return config.get(section, option)


def write_cache(section, option, content, filepath):
    """
    内容的本地缓存
    :param section: str: 缓存的板块
    :param option: str: 缓存的名称
    :param content: str: 保存的内容
    :param filepath: str: 文件路径
    """
    # Create a new configuration object
    config = configparser.ConfigParser()
    config.read(filepath + '.ini')
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, option, content)
    # Write the configuration file to disk
    with open(filepath + '.ini', 'w') as configfile:
        config.write(configfile)
