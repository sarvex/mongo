/**
 *    Copyright (C) 2023-present MongoDB, Inc.
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the Server Side Public License, version 1,
 *    as published by MongoDB, Inc.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    Server Side Public License for more details.
 *
 *    You should have received a copy of the Server Side Public License
 *    along with this program. If not, see
 *    <http://www.mongodb.com/licensing/server-side-public-license>.
 *
 *    As a special exception, the copyright holders give permission to link the
 *    code of portions of this program with the OpenSSL library under certain
 *    conditions as described in each individual source file and distribute
 *    linked combinations including the program with the OpenSSL library. You
 *    must comply with the Server Side Public License in all respects for
 *    all of the code used other than as permitted herein. If you modify file(s)
 *    with this exception, you may extend this exception to your version of the
 *    file(s), but you are not obligated to do so. If you do not wish to do so,
 *    delete this exception statement from your version. If you delete this
 *    exception statement from all source files in the program, then also delete
 *    it in the license file.
 */

#pragma once

#include <boost/smart_ptr/intrusive_ptr.hpp>

#include "mongo/db/pipeline/document_source_change_stream.h"
#include "mongo/db/pipeline/document_source_change_stream_gen.h"
#include "mongo/db/pipeline/expression_context.h"
#include "mongo/db/pipeline/resume_token.h"

namespace mongo {

namespace change_stream {
/**
 * Extracts the resume token from the given spec. If a 'startAtOperationTime' is specified,
 * returns the equivalent high-watermark token. This method should only ever be called on a spec
 * where one of 'resumeAfter', 'startAfter', or 'startAtOperationTime' is populated.
 */
ResumeTokenData resolveResumeTokenFromSpec(const boost::intrusive_ptr<ExpressionContext>& expCtx,
                                           const DocumentSourceChangeStreamSpec& spec);

/**
 * Represents the change stream operation types that are NOT guarded behind the 'showExpandedEvents'
 * flag.
 */
static const std::set<StringData> kClassicOperationTypes =
    std::set<StringData>{DocumentSourceChangeStream::kUpdateOpType,
                         DocumentSourceChangeStream::kDeleteOpType,
                         DocumentSourceChangeStream::kReplaceOpType,
                         DocumentSourceChangeStream::kInsertOpType,
                         DocumentSourceChangeStream::kDropCollectionOpType,
                         DocumentSourceChangeStream::kRenameCollectionOpType,
                         DocumentSourceChangeStream::kDropDatabaseOpType,
                         DocumentSourceChangeStream::kInvalidateOpType,
                         DocumentSourceChangeStream::kReshardBeginOpType,
                         DocumentSourceChangeStream::kReshardDoneCatchUpOpType,
                         DocumentSourceChangeStream::kNewShardDetectedOpType};

}  // namespace change_stream
}  // namespace mongo
