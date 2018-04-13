#!/usr/bin/env/python
# -*- coding: utf-8 -*-

###
### Author:  Chris Iatrou (ichrispa@core-vector.net)
### Version: rev 13
###
### This program was created for educational purposes and has been
### contributed to the open62541 project by the author. All licensing
### terms for this source is inherited by the terms and conditions
### specified for by the open62541 project (see the projects readme
### file for more information on the LGPL terms and restrictions).
###
### This program is not meant to be used in a production environment. The
### author is not liable for any complications arising due to the use of
### this program.
###

import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
import xml.dom.minidom as dom

from constants import *
from base64 import *

import six

if sys.version_info[0] >= 3:
    # strings are already parsed to unicode
    def unicode(s):
        return s


def getNextElementNode(xmlvalue):
    if xmlvalue == None:
        return None
    xmlvalue = xmlvalue.nextSibling
    while not xmlvalue == None and not xmlvalue.nodeType == xmlvalue.ELEMENT_NODE:
        xmlvalue = xmlvalue.nextSibling
    return xmlvalue

def valueIsInternalType(valueTypeString):
    return valueTypeString.lower() in ['boolean', 'number', 'int32', 'uint32', 'int16', 'uint16',
                   'int64', 'uint64', 'byte', 'sbyte', 'float', 'double',
                   'string', 'bytestring', 'localizedtext', 'statuscode',
                   'diagnosticinfo', 'nodeid', 'guid', 'datetime',
                   'qualifiedname', 'expandednodeid', 'xmlelement', 'integer', 'uinteger']

class Value(object):
    def __init__(self, xmlelement=None):
        self.value = None
        self.numericRepresentation = 0
        self.alias = None
        self.dataType = None
        self.encodingRule = []
        self.isInternal = False
        if xmlelement:
            self.parseXML(xmlelement)

    def getValueFieldByAlias(self, fieldname):
        if not isinstance(self.value, list):
            return None
        if not isinstance(self.value[0], Value):
            return None
        for val in self.value:
            if val.alias() == fieldname:
                return val.value
        return None

    def getTypeByString(self, stringName, encodingRule):
        stringName = str(stringName.lower())
        if stringName == 'boolean':
            t = Boolean()
        elif stringName == 'number':
            t = Number()
        elif stringName == 'integer':
            t = Integer()
        elif stringName == 'uinteger':
            t = UInteger()
        elif stringName == 'int32':
            t = Int32()
        elif stringName == 'uint32':
            t = UInt32()
        elif stringName == 'int16':
            t = Int16()
        elif stringName == 'uint16':
            t = UInt16()
        elif stringName == 'int64':
            t = Int64()
        elif stringName == 'uint64':
            t = UInt64()
        elif stringName == 'byte':
            t = Byte()
        elif stringName == 'sbyte':
            t = SByte()
        elif stringName == 'float':
            t = Float()
        elif stringName == 'double':
            t = Double()
        elif stringName == 'string':
            t = String()
        elif stringName == 'bytestring':
            t = ByteString()
        elif stringName == 'localizedtext':
            t = LocalizedText()
        elif stringName == 'statuscode':
            t = StatusCode()
        elif stringName == 'diagnosticinfo':
            t = DiagnosticInfo()
        elif stringName == 'nodeid':
            t = NodeId()
        elif stringName == 'guid':
            t = Guid()
        elif stringName == 'datetime':
            t = DateTime()
        elif stringName == 'qualifiedname':
            t = QualifiedName()
        elif stringName == 'expandednodeid':
            t = ExpandedNodeId()
        elif stringName == 'xmlelement':
            t = XmlElement()
        else:
            logger.debug("No class representing stringName " + stringName + " was found. Cannot create builtinType.")
            return None
        t.encodingRule = encodingRule
        return t

    def checkXML(self, xmlvalue):
        if xmlvalue == None or xmlvalue.nodeType != xmlvalue.ELEMENT_NODE:
            logger.error("Expected XML Element, but got junk...")
            return

    def parseXML(self, xmlvalue):
        raise Exception("Cannot parse arbitrary value of no type.")

    def parseXMLEncoding(self, xmlvalue, parentDataTypeNode, parent):
        self.checkXML(xmlvalue)
        if not "value" in xmlvalue.localName.lower():
            logger.error("Expected <Value> , but found " + xmlvalue.localName + \
                         " instead. Value will not be parsed.")
            return

        if len(xmlvalue.childNodes) == 0:
            logger.error("Expected childnodes for value, but none were found...")
            return

        for n in xmlvalue.childNodes:
            if n.nodeType == n.ELEMENT_NODE:
                xmlvalue = n
                break

        if "ListOf" in xmlvalue.localName:
            self.value = []
            for el in xmlvalue.childNodes:
                if not el.nodeType == el.ELEMENT_NODE:
                    continue
                val = self.__parseXMLSingleValue(el, parentDataTypeNode, parent)
                if val is None:
                    self.value = []
                    return
                self.value.append(val)
        else:
            self.value = [self.__parseXMLSingleValue(xmlvalue, parentDataTypeNode, parent)]

    def __parseXMLSingleValue(self, xmlvalue, parentDataTypeNode, parent, alias=None):
        definition = parentDataTypeNode.getDefinition()

        if isinstance(definition, six.string_types):
            if (alias is not None and alias != xmlvalue.localName) or (alias is None and definition != xmlvalue.localName):
                # TODO: Node 15960 defines datatype as DateTime, but uses String for the value.
                if not (definition == "DateTime" and xmlvalue.localName == "String"):
                    logger.error(str(parent.id) + ": Expected XML '<Value><{} ..>' but got '<Value><{} ..>".format(definition, xmlvalue.localName))
                    return None
            t = self.getTypeByString(definition, [definition])
            t.alias = alias
            t.parseXML(xmlvalue)
            t.isInternal = True
            return t
        elif definition.isEnum:
            if not xmlvalue.localName == "Int32":
                logger.error(str(parent.id) + ": Expected XML '<Value><Int32 ..>' but got '<Value><{} ..>".format(xmlvalue.localName))
                return None
            else:
                t = self.getTypeByString("Int32", ["Int32"])
                t.alias = alias
                t.parseXML(xmlvalue)
                t.isInternal = True
                return t
        else:
            if not xmlvalue.localName == "ExtensionObject":
                logger.error(str(parent.id) + ": Expected XML tag <ExtensionObject> for multipart type, but found " + xmlvalue.localName + " instead.")
                return None

            try:
                extObj =  ExtensionObject(parentDataTypeNode)
                extObj.value = self.__parseExtensionObectWithDefinition(extObj, xmlvalue, parent)
                return extObj
            except Exception as ex:
                logger.error(str(parent.id) + ": Parsing ExtensionObject failed with error: " + str(ex))
                return None

    def __parseExtensionObectWithDefinition(self, extObj, xmlelement, parent):
        from nodes import DataTypeDefinition
        if extObj.encodingRule == None:
            raise Exception("Can not parse XML for extension object without definition.")
        if not isinstance(extObj.dataType.getDefinition(), DataTypeDefinition):
            raise Exception("Datatype of variable needs to be an instance of DataTypeDefinition")


        etype = xmlelement.getElementsByTagName("TypeId")
        if len(etype) == 0:
            raise Exception("Did not find <TypeId> for ExtensionObject")
        etype = etype[0].getElementsByTagName("Identifier")
        if len(etype) == 0:
            raise Exception("Did not find <Identifier> for ExtensionObject")

        extObj.typeId = NodeId(etype[0].firstChild.data.strip(' \t\n\r'))

        ebody = xmlelement.getElementsByTagName("Body")
        if len(ebody) == 0:
            raise Exception("Did not find <Body> for ExtensionObject")
        ebody = ebody[0]

        # Body must contain an Object of type 'DataType' as defined in Variable
        ebodypart = ebody.firstChild
        if not ebodypart.nodeType == ebodypart.ELEMENT_NODE:
            ebodypart = getNextElementNode(ebodypart)
        if ebodypart == None:
            raise Exception("Expected ExtensionObject to hold a variable of type " + str(extObj.dataType.browseName) + " but found nothing.")

        if not ebodypart.localName == extObj.dataType.browseName.name:
            raise Exception("Expected ExtensionObject to hold a variable of type " + str(extObj.dataType.browseName) + " but found " +
                            str(ebodypart.localName) + " instead.")
        extObj.alias = ebodypart.localName

        value = []
        definition = extObj.dataType.getDefinition()

        fieldList = {}

        for x in ebodypart.childNodes:
            if x.nodeType != x.ELEMENT_NODE:
                continue
            fieldList[x.localName] = x

        for field in definition.fields:
            if field.name in fieldList:
                x = fieldList[field.name]
                value.append([field, self.__parseXMLSingleValue(x, field.dataType, parent, alias=field.name)])
            else:
                logger.warn("Field {} not defined in extension object".format(field.name))
                value.append([field, None])

        return value


    def __str__(self):
        return self.__class__.__name__ + "(" + str(self.value) + ")"

    def __repr__(self):
        return self.__str__()

#################
# Builtin Types #
#################

class Boolean(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_BOOLEAN
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        # Expect <Boolean>value</Boolean> or
        #        <Aliasname>value</Aliasname>
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            self.value = "false"  # Catch XML <Boolean /> by setting the value to a default
        else:
            if "false" in unicode(xmlvalue.firstChild.data).lower():
                self.value = "false"
            else:
                self.value = "true"

class Number(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_NUMBER
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        # Expect <Int16>value</Int16> or any other valid number type, or
        #        <Aliasname>value</Aliasname>
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            self.value = 0  # Catch XML <Int16 /> by setting the value to a default
        else:
            self.value = int(unicode(xmlvalue.firstChild.data))

class Integer(Number):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_INTEGER
        if xmlelement:
            self.parseXML(xmlelement)

class UInteger(Number):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_UINTEGER
        if xmlelement:
            self.parseXML(xmlelement)

class Byte(UInteger):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_BYTE
        if xmlelement:
            self.parseXML(xmlelement)

class SByte(Integer):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_SBYTE
        if xmlelement:
            self.parseXML(xmlelement)

class Int16(Integer):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_INT16
        if xmlelement:
            self.parseXML(xmlelement)

class UInt16(UInteger):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_UINT16
        if xmlelement:
            self.parseXML(xmlelement)

class Int32(Integer):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_INT32
        if xmlelement:
            self.parseXML(xmlelement)

class UInt32(UInteger):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_UINT32
        if xmlelement:
            self.parseXML(xmlelement)

class Int64(Integer):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_INT64
        if xmlelement:
            self.parseXML(xmlelement)

class UInt64(UInteger):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_UINT64
        if xmlelement:
            self.parseXML(xmlelement)

class Float(Number):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_FLOAT
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        # Expect <Float>value</Float> or
        #        <Aliasname>value</Aliasname>
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            self.value = 0.0  # Catch XML <Float /> by setting the value to a default
        else:
            self.value = float(unicode(xmlvalue.firstChild.data))

class Double(Float):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_DOUBLE
        if xmlelement:
            self.parseXML(xmlelement)

class String(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_STRING
        if xmlelement:
            self.parseXML(xmlelement)

    def pack(self):
        bin = structpack("I", len(unicode(self.value)))
        bin = bin + str(self.value)
        return bin

    def parseXML(self, xmlvalue):
        # Expect <String>value</String> or
        #        <Aliasname>value</Aliasname>
        if not isinstance(xmlvalue, dom.Element):
            self.value = xmlvalue
            return
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            self.value = ""  # Catch XML <String /> by setting the value to a default
        else:
            self.value = unicode(xmlvalue.firstChild.data)

class XmlElement(String):
    def __init__(self, xmlelement=None):
        Value.__init__(self, xmlelement)
        self.numericRepresentation = BUILTINTYPE_TYPEID_XMLELEMENT

class ByteString(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self, xmlelement)
        self.numericRepresentation = BUILTINTYPE_TYPEID_BYTESTRING

    def parseXML(self, xmlvalue):
        # Expect <ByteString>value</ByteString>
        if not isinstance(xmlvalue, dom.Element):
            self.value = xmlvalue
            return
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            self.value = []  # Catch XML <ByteString /> by setting the value to a default
        else:
            self.value = b64decode(xmlvalue.firstChild.data).decode("utf-8")

class ExtensionObject(Value):
    def __init__(self, dataType=None, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_EXTENSIONOBJECT
        self.dataType = dataType
        if dataType is not None:
            self.encodingRule = dataType.definition
            
        self.typeId = None
                
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlelement):
        pass

    def __str__(self):
        return "'" + self.alias() + "':" + self.stringRepresentation + "(" + str(self.value) + ")"

class LocalizedText(Value):
    def __init__(self, xmlvalue=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_LOCALIZEDTEXT
        self.locale = ''
        self.text = ''
        if xmlvalue:
            self.parseXML(xmlvalue)

    def parseXML(self, xmlvalue):
        # Expect <LocalizedText> or <AliasName>
        #          <Locale>xx_XX</Locale>
        #          <Text>TextText</Text>
        #        <LocalizedText> or </AliasName>
        if not isinstance(xmlvalue, dom.Element):
            self.text = xmlvalue
            return
        self.checkXML(xmlvalue)
        tmp = xmlvalue.getElementsByTagName("Locale")
        if len(tmp) > 0 and tmp[0].firstChild != None:
            self.locale = tmp[0].firstChild.data.strip(' \t\n\r')
        tmp = xmlvalue.getElementsByTagName("Text")
        if len(tmp) > 0 and tmp[0].firstChild != None:
            self.text = tmp[0].firstChild.data.strip(' \t\n\r')

    def __str__(self):
        if self.locale is not None and len(self.locale) > 0:
            return "(" + self.locale + ":" + self.text + ")"
        else:
            return self.text

class NodeId(Value):
    def __init__(self, idstring=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_NODEID
        self.i = None
        self.b = None
        self.g = None
        self.s = None
        self.ns = 0
        self.setFromIdString(idstring)

    def setFromIdString(self, idstring):

        if not idstring:
            self.i = 0
            return

        # The ID will encoding itself appropriatly as string. If multiple ID's
        # (numeric, string, guid) are defined, the order of preference for the ID
        # string is always numeric, guid, bytestring, string. Binary encoding only
        # applies to numeric values (UInt16).
        idparts = idstring.strip().split(";")
        for p in idparts:
            if p[:2] == "ns":
                self.ns = int(p[3:])
            elif p[:2] == "i=":
                self.i = int(p[2:])
            elif p[:2] == "o=":
                self.b = p[2:]
            elif p[:2] == "g=":
                tmp = []
                self.g = p[2:].split("-")
                for i in self.g:
                    i = "0x" + i
                    tmp.append(int(i, 16))
                self.g = tmp
            elif p[:2] == "s=":
                self.s = p[2:]
            else:
                raise Exception("no valid nodeid: " + idstring)

    def parseXML(self, xmlvalue):
        # Expect <NodeId> or <Alias>
        #           <Identifier> # It is unclear whether or not this is manditory. Identifier tags are used in Namespace 0.
        #                ns=x;i=y or similar string representation of id()
        #           </Identifier>
        #        </NodeId> or </Alias>
        if not isinstance(xmlvalue, dom.Element):
            self.text = xmlvalue
            return
        self.checkXML(xmlvalue)

        if self.alias != None:
            if not self.alias == xmlvalue.localName:
                logger.warn(
                    "Expected an aliased XML field called " + self.alias + " but got " + xmlvalue.localName + " instead. This is a parsing error of Value.__parseXMLSingleValue(), will try to continue anyway.")
        else:
            if not self.stringRepresentation == xmlvalue.localName:
                logger.warn(
                    "Expected XML field " + self.stringRepresentation + " but got " + xmlvalue.localName + " instead. This is a parsing error of Value.__parseXMLSingleValue(), will try to continue anyway.")

        # Catch XML <NodeId />
        if xmlvalue.firstChild == None:
            logger.error("No value is given, which is illegal for Node Types...")
            self.value = None
        else:
            # Check if there is an <Identifier> tag
            if len(xmlvalue.getElementsByTagName("Identifier")) != 0:
                xmlvalue = xmlvalue.getElementsByTagName("Identifier")[0]
            self.setFromIdString(unicode(xmlvalue.firstChild.data))

    def __str__(self):
        s = "ns=" + str(self.ns) + ";"
        # Order of preference is numeric, guid, bytestring, string
        if self.i != None:
            return s + "i=" + str(self.i)
        elif self.g != None:
            s = s + "g="
            tmp = []
            for i in self.g:
                tmp.append(hex(i).replace("0x", ""))
            for i in tmp:
                s = s + "-" + i
            return s.replace("g=-", "g=")
        elif self.b != None:
            return s + "b=" + str(self.b)
        elif self.s != None:
            return s + "s=" + str(self.s)

    def __eq__(self, nodeId2):
        return (str(self) == str(nodeId2))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))

class ExpandedNodeId(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_EXPANDEDNODEID
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        self.checkXML(xmlvalue)
        logger.debug("Not implemented", LOG_LEVEL_ERR)

class DateTime(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_DATETIME
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        # Expect <DateTime> or <AliasName>
        #        2013-08-13T21:00:05.0000L
        #        </DateTime> or </AliasName>
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            # Catch XML <DateTime /> by setting the value to a default
            self.value = datetime(2001, 1, 1)
        else:
            timestr = unicode(xmlvalue.firstChild.data)
            # .NET tends to create this garbage %Y-%m-%dT%H:%M:%S.0000z
            # strip everything after the "." away for a posix time_struct
            if "." in timestr:
                timestr = timestr[:timestr.index(".")]
            # If the last character is not numeric, remove it
            while len(timestr) > 0 and not timestr[-1] in "0123456789":
                timestr = timestr[:-1]
            try:
                self.value = datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S")
            except:
                try:
                    self.value = datetime.strptime(timestr, "%Y-%m-%d")
                except:
                    logger.error("Timestring format is illegible. Expected 2001-01-30T21:22:23 or 2001-01-30, but got " + \
                                 timestr + " instead. Time will be defaultet to now()")
                    self.value = datetime(2001, 1, 1)

class QualifiedName(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_QUALIFIEDNAME
        self.ns = 0
        self.name = ''
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        # Expect <QualifiedName> or <AliasName>
        #           <NamespaceIndex>Int16<NamespaceIndex>
        #           <Name>SomeString<Name>
        #        </QualifiedName> or </AliasName>
        if not isinstance(xmlvalue, dom.Element):
            colonindex = xmlvalue.find(":")
            if colonindex == -1:
                self.name = xmlvalue
            else:
                self.name = xmlvalue[colonindex + 1:]
                self.ns = int(xmlvalue[:colonindex])
            return

        self.checkXML(xmlvalue)
        # Is a namespace index passed?
        if len(xmlvalue.getElementsByTagName("NamespaceIndex")) != 0:
            self.ns = int(xmlvalue.getElementsByTagName("NamespaceIndex")[0].firstChild.data)
        if len(xmlvalue.getElementsByTagName("Name")) != 0:
            self.name = xmlvalue.getElementsByTagName("Name")[0].firstChild.data

    def __str__(self):
        return "ns=" + str(self.ns) + ";" + str(self.name)

class StatusCode(UInt32):
    def __init__(self, xmlelement=None):
        Value.__init__(self, xmlelement)
        self.numericRepresentation = BUILTINTYPE_TYPEID_STATUSCODE

class DiagnosticInfo(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_DIAGNOSTICINFO
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        self.checkXML(xmlvalue)
        logger.warn("Not implemented")

class Guid(Value):
    def __init__(self, xmlelement=None):
        Value.__init__(self)
        self.numericRepresentation = BUILTINTYPE_TYPEID_GUID
        if xmlelement:
            self.parseXML(xmlelement)

    def parseXML(self, xmlvalue):
        self.checkXML(xmlvalue)
        if xmlvalue.firstChild == None:
            self.value = [0, 0, 0, 0]  # Catch XML <Guid /> by setting the value to a default
        else:
            self.value = unicode(xmlvalue.firstChild.data)
            self.value = self.value.replace("{", "")
            self.value = self.value.replace("}", "")
            self.value = self.value.split("-")
            tmp = []
            for g in self.value:
                try:
                    tmp.append(int("0x" + g, 16))
                except:
                    logger.error("Invalid formatting of Guid. Expected {01234567-89AB-CDEF-ABCD-0123456789AB}, got " + \
                                 unicode(xmlvalue.firstChild.data))
                    tmp = [0, 0, 0, 0, 0]
            if len(tmp) != 5:
                logger.error("Invalid formatting of Guid. Expected {01234567-89AB-CDEF-ABCD-0123456789AB}, got " + \
                             unicode(xmlvalue.firstChild.data))
                tmp = [0, 0, 0, 0]
            self.value = tmp
