"""Customize node illustrations in memory while keeping the SVG template intact."""

from xml.dom import Node, minidom

SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def _text_nodes(element):
    for child in element.childNodes:
        if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            yield child
        else:
            yield from _text_nodes(child)


def _replace_label_text(label, value):
    # Inkscape may split one label across styled tspan elements.
    content = [part for part in _text_nodes(label) if part.data.strip()]
    if content:
        content[0].replaceWholeText(value)
        for part in content[1:]:
            if part.parentNode is not None:
                part.data = ""
    else:
        label.appendChild(label.ownerDocument.createTextNode(value))


def svg_for_host(svg_data: bytes, host_name: str) -> bytes:
    """Replace the equipment label in either node SVG, preserving its styling."""
    with minidom.parseString(svg_data) as document:
        labels = document.getElementsByTagNameNS(SVG_NAMESPACE, "text")
        # Inkscape may move the label outside g43 when editing the x86 artwork.
        label = next((item for item in labels if item.getAttribute("id") == "host_name"), None)
        if label is None:
            label = next((item for item in labels if item.getAttribute("id") == "text35"), None)
        if label is None:
            label = next((item for item in labels
                          if "".join(part.data for part in _text_nodes(item)).strip() == "X86-XXX"), None)
        if label is None:
            return svg_data

        _replace_label_text(label, host_name)
        return document.toxml(encoding="utf-8")


def svg_for_subsystem_id(svg_data: bytes, subsystem_id: str | None) -> bytes:
    """Fill the SVG's WR label, or omit it for TimeSorter, without moving it."""
    with minidom.parseString(svg_data) as document:
        label = next((element for element in document.getElementsByTagName('*')
                      if element.getAttribute('id') in ('whiterabbit_id', 'whiterubbit_id')), None)
        if label is None:
            return svg_data
        if subsystem_id is None:
            label.parentNode.removeChild(label)
        else:
            _replace_label_text(label, f'WR: {subsystem_id}')
        return document.toxml(encoding='utf-8')


def svg_for_power_led(svg_data: bytes, color: str) -> bytes:
    """Change only led_power's fill, including Inkscape's inline style override."""
    with minidom.parseString(svg_data) as document:
        for element in document.getElementsByTagName('*'):
            if element.getAttribute('id') != 'led_power':
                continue
            element.setAttribute('fill', color)
            if element.hasAttribute('style'):
                declarations = [part for part in element.getAttribute('style').split(';')
                                if part.strip() and part.partition(':')[0].strip().lower() != 'fill']
                declarations.append(f'fill:{color}')
                element.setAttribute('style', ';'.join(declarations))
            return document.toxml(encoding='utf-8')
    return svg_data
