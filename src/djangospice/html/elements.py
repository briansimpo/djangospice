
from __future__ import annotations

from typing import Any

from .element import HTMLElement
from .helpers import create_element_class


# ----------------------------------------------------------------------
# Document
# ----------------------------------------------------------------------

class Html(HTMLElement):
    tag_name = "html"


class Head(HTMLElement):
    tag_name = "head"


class Title(HTMLElement):
    tag_name = "title"


class Base(HTMLElement):
    tag_name = "base"


class Link(HTMLElement):
    tag_name = "link"


class Meta(HTMLElement):
    tag_name = "meta"


class Style(HTMLElement):
    tag_name = "style"


class Body(HTMLElement):
    tag_name = "body"


# ----------------------------------------------------------------------
# Sectioning
# ----------------------------------------------------------------------

class Article(HTMLElement):
    tag_name = "article"


class Section(HTMLElement):
    tag_name = "section"


class Nav(HTMLElement):
    tag_name = "nav"


class Aside(HTMLElement):
    tag_name = "aside"


class Header(HTMLElement):
    tag_name = "header"


class Footer(HTMLElement):
    tag_name = "footer"


class Address(HTMLElement):
    tag_name = "address"


class Main(HTMLElement):
    tag_name = "main"


# ----------------------------------------------------------------------
# Headings
# ----------------------------------------------------------------------

class H1(HTMLElement):
    tag_name = "h1"


class H2(HTMLElement):
    tag_name = "h2"


class H3(HTMLElement):
    tag_name = "h3"


class H4(HTMLElement):
    tag_name = "h4"


class H5(HTMLElement):
    tag_name = "h5"


class H6(HTMLElement):
    tag_name = "h6"


# ----------------------------------------------------------------------
# Text content
# ----------------------------------------------------------------------

class P(HTMLElement):
    tag_name = "p"


class Hr(HTMLElement):
    tag_name = "hr"


class Pre(HTMLElement):
    tag_name = "pre"


class Blockquote(HTMLElement):
    tag_name = "blockquote"


class Ol(HTMLElement):
    tag_name = "ol"


class Ul(HTMLElement):
    tag_name = "ul"


class Li(HTMLElement):
    tag_name = "li"


class Dl(HTMLElement):
    tag_name = "dl"


class Dt(HTMLElement):
    tag_name = "dt"


class Dd(HTMLElement):
    tag_name = "dd"


# ----------------------------------------------------------------------
# Inline text semantics
# ----------------------------------------------------------------------

class Figure(HTMLElement):
    tag_name = "figure"


class Figcaption(HTMLElement):
    tag_name = "figcaption"


class Div(HTMLElement):
    tag_name = "div"


class A(HTMLElement):
    tag_name = "a"


class Em(HTMLElement):
    tag_name = "em"


class Strong(HTMLElement):
    tag_name = "strong"


class Small(HTMLElement):
    tag_name = "small"


class S(HTMLElement):
    tag_name = "s"


class Cite(HTMLElement):
    tag_name = "cite"


class Q(HTMLElement):
    tag_name = "q"


class Dfn(HTMLElement):
    tag_name = "dfn"


class Abbr(HTMLElement):
    tag_name = "abbr"


class Data(HTMLElement):
    tag_name = "data"


class Time(HTMLElement):
    tag_name = "time"


class Code(HTMLElement):
    tag_name = "code"


class Var(HTMLElement):
    tag_name = "var"


class Samp(HTMLElement):
    tag_name = "samp"


class Kbd(HTMLElement):
    tag_name = "kbd"


class Sub(HTMLElement):
    tag_name = "sub"


class Sup(HTMLElement):
    tag_name = "sup"


class I(HTMLElement):
    tag_name = "i"


class B(HTMLElement):
    tag_name = "b"


class U(HTMLElement):
    tag_name = "u"


class Mark(HTMLElement):
    tag_name = "mark"


class Ruby(HTMLElement):
    tag_name = "ruby"


class Rt(HTMLElement):
    tag_name = "rt"


class Rp(HTMLElement):
    tag_name = "rp"


class Bdi(HTMLElement):
    tag_name = "bdi"


class Bdo(HTMLElement):
    tag_name = "bdo"


class Span(HTMLElement):
    tag_name = "span"


class Br(HTMLElement):
    tag_name = "br"


class Wbr(HTMLElement):
    tag_name = "wbr"


class Ins(HTMLElement):
    tag_name = "ins"


class Del(HTMLElement):
    tag_name = "del"


# ----------------------------------------------------------------------
# Media and embedded content
# ----------------------------------------------------------------------

class Picture(HTMLElement):
    tag_name = "picture"


class Source(HTMLElement):
    tag_name = "source"


class Img(HTMLElement):
    tag_name = "img"


class Iframe(HTMLElement):
    tag_name = "iframe"


class Embed(HTMLElement):
    tag_name = "embed"


class Object(HTMLElement):
    tag_name = "object"


class Param(HTMLElement):
    tag_name = "param"


class Video(HTMLElement):
    tag_name = "video"


class Audio(HTMLElement):
    tag_name = "audio"


class Track(HTMLElement):
    tag_name = "track"


class Map(HTMLElement):
    tag_name = "map"


class Area(HTMLElement):
    tag_name = "area"


# ----------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------

class Table(HTMLElement):
    tag_name = "table"


class Caption(HTMLElement):
    tag_name = "caption"


class Colgroup(HTMLElement):
    tag_name = "colgroup"


class Col(HTMLElement):
    tag_name = "col"


class Tbody(HTMLElement):
    tag_name = "tbody"


class Thead(HTMLElement):
    tag_name = "thead"


class Tfoot(HTMLElement):
    tag_name = "tfoot"


class Tr(HTMLElement):
    tag_name = "tr"


class Td(HTMLElement):
    tag_name = "td"


class Th(HTMLElement):
    tag_name = "th"


# ----------------------------------------------------------------------
# Forms
# ----------------------------------------------------------------------

class Form(HTMLElement):
    tag_name = "form"


class Label(HTMLElement):
    tag_name = "label"


class Input(HTMLElement):
    tag_name = "input"


class Button(HTMLElement):
    tag_name = "button"


class Select(HTMLElement):
    tag_name = "select"


class Datalist(HTMLElement):
    tag_name = "datalist"


class Optgroup(HTMLElement):
    tag_name = "optgroup"


class Option(HTMLElement):
    tag_name = "option"


class Textarea(HTMLElement):
    tag_name = "textarea"


class Output(HTMLElement):
    tag_name = "output"


class Progress(HTMLElement):
    tag_name = "progress"


class Meter(HTMLElement):
    tag_name = "meter"


class Fieldset(HTMLElement):
    tag_name = "fieldset"


class Legend(HTMLElement):
    tag_name = "legend"


# ----------------------------------------------------------------------
# Interactive elements
# ----------------------------------------------------------------------

class Details(HTMLElement):
    tag_name = "details"


class Summary(HTMLElement):
    tag_name = "summary"


class Dialog(HTMLElement):
    tag_name = "dialog"


# ----------------------------------------------------------------------
# Scripting and graphics
# ----------------------------------------------------------------------

class Script(HTMLElement):
    tag_name = "script"


class Noscript(HTMLElement):
    tag_name = "noscript"


class Template(HTMLElement):
    tag_name = "template"


class Canvas(HTMLElement):
    tag_name = "canvas"


