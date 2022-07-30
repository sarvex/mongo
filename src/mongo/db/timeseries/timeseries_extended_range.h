/**
 *    Copyright (C) 2022-present MongoDB, Inc.
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

#include "mongo/bson/bsonobj.h"
#include "mongo/db/catalog/collection.h"
#include "mongo/db/timeseries/timeseries_gen.h"

namespace mongo::timeseries {

/**
 * Determines whether the given 'date' is outside the standard supported range and requires extended
 * range support. Standard range dates can be expressed as a number of seconds since the Unix epoch
 * in 31 unsigned bits.
 */
bool dateOutsideStandardRange(Date_t date);

/**
 * Determines whether any of the given measurements have timeField values that lie outside the
 * standard range.
 */
bool measurementsHaveDateOutsideStandardRange(const TimeseriesOptions& options,
                                              const std::vector<BSONObj>& measurements);

/**
 * Uses a heuristic to determine whether a given time-series collection may contain measurements
 * with dates that fall outside the standard range.
 */
bool collectionMayRequireExtendedRangeSupport(OperationContext* opCtx,
                                              const CollectionPtr& collection);

/**
 * Determines whether a time-series collection has an index primarily ordered by a time field. This
 * excludes the clustered index, and is testing specifically if an index's key pattern's first field
 * is either control.min.<timeField> or control.max.<timeField>.
 */
bool collectionHasTimeIndex(OperationContext* opCtx, const Collection& collection);
}  // namespace mongo::timeseries
