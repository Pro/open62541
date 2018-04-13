#!/usr/bin/env/python
# -*- coding: utf-8 -*-

###
### Authors:
### - Chris Iatrou (ichrispa@core-vector.net)
### - Julius Pfrommer
### - Stefan Profanter (profanter@fortiss.org)
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

from __future__ import print_function
import string
from os.path import basename
import logging
import codecs
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

logger = logging.getLogger(__name__)

from constants import *
from nodes import *
from nodeset import *
from backend_open62541_nodes import generateNodeCode_begin, generateNodeCode_finish, generateReferenceCode

# Kahn's algorithm: https://algocoding.wordpress.com/2015/04/05/topological-sorting-python/
def sortNodes(nodeset):

    # Ensure that every reference has an inverse reference in the target
    for u in nodeset.nodes.values():
        for ref in u.references:
            back = Reference(ref.target, ref.referenceType, ref.source, not ref.isForward)
            nodeset.nodes[ref.target].references.add(back) # ref set does not make a duplicate entry

    # reverse hastypedefinition references to treat only forward references
    hasTypeDef = NodeId("ns=0;i=40")
    for u in nodeset.nodes.values():
        for ref in u.references:
            if ref.referenceType == hasTypeDef:
                ref.isForward = not ref.isForward

    # Only hierarchical types...
    relevant_refs = nodeset.getRelevantOrderingReferences()

    # determine in-degree of unfulfilled references
    L = [node for node in nodeset.nodes.values() if node.hidden]  # ordered list of nodes
    R = {node.id: node for node in nodeset.nodes.values() if not node.hidden} # remaining nodes
    in_degree = {id: 0 for id in R.keys()}
    for u in R.values(): # for each node
        for ref in u.references:
            if not ref.referenceType in relevant_refs:
                continue
            if nodeset.nodes[ref.target].hidden:
                continue
            if ref.isForward:
                continue
            in_degree[u.id] += 1

    # Print ReferenceType and DataType nodes first. They may be required even
    # though there is no reference to them. For example if the referencetype is
    # used in a reference, it must exist. A Variable node may point to a
    # DataTypeNode in the datatype attribute and not via an explicit reference.

    Q = {node for node in R.values() if in_degree[node.id] == 0 and
         (isinstance(node, ReferenceTypeNode) or isinstance(node, DataTypeNode))}
    while Q:
        u = Q.pop() # choose node of zero in-degree and 'remove' it from graph
        L.append(u)
        del R[u.id]

        for ref in u.references:
            if not ref.referenceType in relevant_refs:
                continue
            if nodeset.nodes[ref.target].hidden:
                continue
            if not ref.isForward:
                continue
            in_degree[ref.target] -= 1
            if in_degree[ref.target] == 0:
                Q.add(R[ref.target])

    # Order the remaining nodes
    Q = {node for node in R.values() if in_degree[node.id] == 0}
    while Q:
        u = Q.pop() # choose node of zero in-degree and 'remove' it from graph
        L.append(u)
        del R[u.id]

        for ref in u.references:
            if not ref.referenceType in relevant_refs:
                continue
            if nodeset.nodes[ref.target].hidden:
                continue
            if not ref.isForward:
                continue
            in_degree[ref.target] -= 1
            if in_degree[ref.target] == 0:
                Q.add(R[ref.target])

    # reverse hastype references
    for u in nodeset.nodes.values():
        for ref in u.references:
            if ref.referenceType == hasTypeDef:
                ref.isForward = not ref.isForward

    if len(L) != len(nodeset.nodes.values()):
        print(len(L))
        stillOpen = ""
        for id in in_degree:
            if in_degree[id] == 0:
                continue
            node = nodeset.nodes[id]
            stillOpen += node.browseName.name + "/" + str(node.id) + " = " + str(in_degree[id]) + \
                                                                         " " + str(node.references) + "\r\n"
        raise Exception("Node graph is circular on the specified references. Still open nodes:\r\n" + stillOpen)
    return L

###################
# Generate C Code #
###################

def generateCustomDatatypesDefinition(nodeset, typesArray):
    # See examples/custom_datatype/custom_datatype.h on how the definition should look
    code = []

    for datatype in nodeset.getCustomDatatypes().keys():
        if datatype.getDefinition().isEnum:
            continue

        name = nodeset.getCustomDatatypeName(datatype)
        code.append("/* ----------------------------- */")
        code.append("typedef struct {")
        for field in datatype.getDefinition().fields:
            if field.dataType.id.ns != 0:
                raise Exception("Custom datatypes currently only can be used with types from NS0")
            code.append("UA_{type} {name};".format(
                type=field.dataType.definition.__name__, name=field.name))
        code.append("} {};".format(name))

        code.append("\nstatic UA_DataTypeMember {name}_members[{size}] = {".format(
            name=name, size=str(len(datatype.getDefinition().fields))
        ))
        prevField = None
        for i, field in enumerate(datatype.getDefinition().fields):
            padding = "0"
            if prevField is not None:
                padding = "offsetof({name},{field_name}) - offsetof({name}, {prev_name}) - sizeof(UA_{prev_type})".format(
                    name=name,
                    field_name=field.name,
                    prev_name=prevField.name,
                    prev_type=prevField.dataType.definition.__name__
                )
            # TODO handle types from custom types array not in NS0
            code.append("""/* {memberName} */
    {
        UA_TYPENAME("{memberName}")
        {memberTypeIndex},
        {padding},
        {namespaceZero},    
        {isArray} 
    }{sep}   
            """.format(
                memberName=field.name,
                memberTypeIndex="UA_TYPES_" + field.dataType.definition.__name__.upper(),
                padding=padding,
                namespaceZero="true",
                isArray="true" if field.valueRank > 0 else "false",
                sep="," if i < len(datatype.getDefinition().fields)-1 else ""
            ))
            code.append("};")

            if datatype.id.i is None:
                raise Exception("Custom datatypes currently only support numeric node ids")
            typeId = "{{ns}, UA_NODEIDTYPE_NUMERIC, {id}}".format(ns=datatype.id.ns, id=datatype.id.i)

            code.append("""static const UA_DataType {typeName}Type = {
    UA_TYPENAME("{typeName}")
    {typeId},
    sizeof({typeName}),
    {typeIndex},
    {membersSize},
    false,
    {pointerFree},
    false,
    {binaryEncodingId},
    {typeName}_members
};""".format(
                typeName=name,
                typeId=typeId,
                typeIndex=TODO,
                membersSize=len(datatype.getDefinition().fields),
                pointerFree=TODO,
                binaryEncodingId=TODO,
                type=field.dataType.definition.__name__, name=field.name))
            prevField = field

    return "\n".join(code)

def generateOpen62541Header(nodeset, outfilename, typesArray=[]):

    outfilebase = basename(outfilename)
    # Printing functions
    outfileh = codecs.open(outfilename + ".h", r"w+", encoding='utf-8')

    def writeh(line):
        print(unicode(line), end='\n', file=outfileh)


    additionalHeaders = ""
    if len(typesArray) > 0:
        for arr in set(typesArray):
            if arr == "UA_TYPES":
                continue
            additionalHeaders += """#include "%s_generated.h"\n""" % arr.lower()

    # Print the preamble of the generated code
    writeh("""/* WARNING: This is a generated file.
 * Any manual changes will be overwritten. */

#ifndef %s_H_
#define %s_H_
""" % (outfilebase.upper(), outfilebase.upper()))
    #     if internal_headers:
    #         writeh("""
    # #ifdef UA_NO_AMALGAMATION
    # # include "ua_server.h"
    # # include "ua_types_encoding_binary.h"
    # #else
    # # include "open62541.h"
    #
    # /* The following declarations are in the open62541.c file so here's needed when compiling nodesets externally */
    #
    # # ifndef UA_Nodestore_remove //this definition is needed to hide this code in the amalgamated .c file
    #
    # typedef UA_StatusCode (*UA_exchangeEncodeBuffer)(void *handle, UA_Byte **bufPos,
    #                                                  const UA_Byte **bufEnd);
    #
    # UA_StatusCode
    # UA_encodeBinary(const void *src, const UA_DataType *type,
    #                 UA_Byte **bufPos, const UA_Byte **bufEnd,
    #                 UA_exchangeEncodeBuffer exchangeCallback,
    #                 void *exchangeHandle) UA_FUNC_ATTR_WARN_UNUSED_RESULT;
    #
    # UA_StatusCode
    # UA_decodeBinary(const UA_ByteString *src, size_t *offset, void *dst,
    #                 const UA_DataType *type, size_t customTypesSize,
    #                 const UA_DataType *customTypes) UA_FUNC_ATTR_WARN_UNUSED_RESULT;
    #
    # size_t
    # UA_calcSizeBinary(void *p, const UA_DataType *type);
    #
    # const UA_DataType *
    # UA_findDataTypeByBinary(const UA_NodeId *typeId);
    #
    # # endif // UA_Nodestore_remove
    #
    # #endif
    #
    # %s
    # """ % (additionalHeaders))
    #     else:
    writeh("""
#include "open62541.h"
""")

    writeh("""
#ifdef __cplusplus
extern "C" {
#endif

/* Custom Datatypes */

%s

extern UA_StatusCode %s(UA_Server *server);

#ifdef __cplusplus
}
#endif

#endif /* %s_H_ */""" % \
           (generateCustomDatatypesDefinition(nodeset, typesArray), outfilebase, outfilebase.upper()))

    outfileh.close()

def generateOpen62541Code(nodeset, outfilename, generate_ns0=False, internal_headers=False, typesArray=[], max_string_length=0):
    outfilebase = basename(outfilename)
    outfilec = StringIO()


    def writec(line):
        print(unicode(line), end='\n', file=outfilec)

    writec("""/* WARNING: This is a generated file.
 * Any manual changes will be overwritten. */

#include "%s.h"
""" % (outfilebase))

    # Loop over the sorted nodes
    logger.info("Reordering nodes for minimal dependencies during printing")
    sorted_nodes = sortNodes(nodeset)
    logger.info("Writing code for nodes and references")
    functionNumber = 0

    parentreftypes = getSubTypesOf(nodeset, nodeset.getNodeByBrowseName("HierarchicalReferences"))
    parentreftypes = list(map(lambda x: x.id, parentreftypes))

    printed_ids = set()
    for node in sorted_nodes:
        printed_ids.add(node.id)

        parentref = node.popParentRef(parentreftypes)
        if not node.hidden:
            writec("\n/* " + str(node.displayName) + " - " + str(node.id) + " */")
            code = generateNodeCode_begin(node, nodeset, max_string_length, generate_ns0, parentref)
            if code is None:
                writec("/* Ignored. No parent */")
                nodeset.hide_node(node.id)
                continue
            else:
                writec("\nstatic UA_StatusCode function_" + outfilebase + "_" + str(functionNumber) + "_begin(UA_Server *server, UA_UInt16* ns) {")
                if isinstance(node, MethodNode):
                    writec("#ifdef UA_ENABLE_METHODCALLS")
                writec(code)

        # Print inverse references leading to this node
        for ref in node.references:
            if ref.target not in printed_ids:
                continue
            if node.hidden and nodeset.nodes[ref.target].hidden:
                continue
            writec(generateReferenceCode(ref))

        if node.hidden:
            continue

        writec("return retVal;")

        if isinstance(node, MethodNode):
            writec("#else")
            writec("return UA_STATUSCODE_GOOD;")
            writec("#endif /* UA_ENABLE_METHODCALLS */")
        writec("}")

        writec("\nstatic UA_StatusCode function_" + outfilebase + "_" + str(functionNumber) + "_finish(UA_Server *server, UA_UInt16* ns) {")

        if isinstance(node, MethodNode):
            writec("#ifdef UA_ENABLE_METHODCALLS")
        writec("return " + generateNodeCode_finish(node))
        if isinstance(node, MethodNode):
            writec("#else")
            writec("return UA_STATUSCODE_GOOD;")
            writec("#endif /* UA_ENABLE_METHODCALLS */")
        writec("}")

        functionNumber = functionNumber + 1

    writec("""
UA_StatusCode %s(UA_Server *server) {
UA_StatusCode retVal = UA_STATUSCODE_GOOD;""" % (outfilebase))

    # Generate namespaces (don't worry about duplicates)
    writec("/* Use namespace ids generated by the server */")
    writec("UA_UInt16 ns[" + str(len(nodeset.namespaces)) + "];")
    for i, nsid in enumerate(nodeset.namespaces):
        nsid = nsid.replace("\"", "\\\"")
        writec("ns[" + str(i) + "] = UA_Server_addNamespace(server, \"" + nsid + "\");")

    for i in range(0, functionNumber):
        writec("retVal |= function_" + outfilebase + "_" + str(i) + "_begin(server, ns);")

    for i in reversed(range(0, functionNumber)):
        writec("retVal |= function_" + outfilebase + "_" + str(i) + "_finish(server, ns);")

    writec("return retVal;\n}")

    fullCode = outfilec.getvalue()
    outfilec.close()

    outfilec = codecs.open(outfilename + ".c", r"w+", encoding='utf-8')
    outfilec.write(fullCode)
    outfilec.close()

    generateOpen62541Header(nodeset, outfilename, typesArray)
