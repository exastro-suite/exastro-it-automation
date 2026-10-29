/*! aws-sdk-js-v3 https://github.com/aws/aws-sdk-js-v3 @license Apache-2.0 license */
var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res, err) => function __init() {
  if (err) throw err[0];
  try {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  } catch (e2) {
    throw err = [e2], e2;
  }
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// node_modules/@smithy/core/dist-es/submodules/serde/util-base64/constants-for-browser.js
var chars, alphabetByEncoding, alphabetByValue, bitsPerLetter, bitsPerByte, maxLetterValue;
var init_constants_for_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-base64/constants-for-browser.js"() {
    chars = `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/`;
    alphabetByEncoding = Object.entries(chars).reduce((acc, [i2, c2]) => {
      acc[c2] = Number(i2);
      return acc;
    }, {});
    alphabetByValue = chars.split("");
    bitsPerLetter = 6;
    bitsPerByte = 8;
    maxLetterValue = 63;
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-base64/fromBase64.browser.js
var fromBase64;
var init_fromBase64_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-base64/fromBase64.browser.js"() {
    init_constants_for_browser();
    fromBase64 = (input) => {
      let totalByteLength = input.length / 4 * 3;
      if (input.slice(-2) === "==") {
        totalByteLength -= 2;
      } else if (input.slice(-1) === "=") {
        totalByteLength--;
      }
      const out = new ArrayBuffer(totalByteLength);
      const dataView = new DataView(out);
      for (let i2 = 0; i2 < input.length; i2 += 4) {
        let bits = 0;
        let bitLength = 0;
        for (let j2 = i2, limit = i2 + 3; j2 <= limit; j2++) {
          if (input[j2] !== "=") {
            if (!(input[j2] in alphabetByEncoding)) {
              throw new TypeError(`Invalid character ${input[j2]} in base64 string.`);
            }
            bits |= alphabetByEncoding[input[j2]] << (limit - j2) * bitsPerLetter;
            bitLength += bitsPerLetter;
          } else {
            bits >>= bitsPerLetter;
          }
        }
        const chunkOffset = i2 / 4 * 3;
        bits >>= bitLength % bitsPerByte;
        const byteLength = Math.floor(bitLength / bitsPerByte);
        for (let k2 = 0; k2 < byteLength; k2++) {
          const offset = (byteLength - k2 - 1) * bitsPerByte;
          dataView.setUint8(chunkOffset + k2, (bits & 255 << offset) >> offset);
        }
      }
      return new Uint8Array(out);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-utf8/fromUtf8.browser.js
var fromUtf8;
var init_fromUtf8_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-utf8/fromUtf8.browser.js"() {
    fromUtf8 = (input) => new TextEncoder().encode(input);
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-base64/toBase64.browser.js
function toBase64(_input) {
  let input;
  if (typeof _input === "string") {
    input = fromUtf8(_input);
  } else {
    input = _input;
  }
  const isArrayLike = typeof input === "object" && typeof input.length === "number";
  const isUint8Array = typeof input === "object" && typeof input.byteOffset === "number" && typeof input.byteLength === "number";
  if (!isArrayLike && !isUint8Array) {
    throw new Error("@smithy/util-base64: toBase64 encoder function only accepts string | Uint8Array.");
  }
  let str = "";
  for (let i2 = 0; i2 < input.length; i2 += 3) {
    let bits = 0;
    let bitLength = 0;
    for (let j2 = i2, limit = Math.min(i2 + 3, input.length); j2 < limit; j2++) {
      bits |= input[j2] << (limit - j2 - 1) * bitsPerByte;
      bitLength += bitsPerByte;
    }
    const bitClusterCount = Math.ceil(bitLength / bitsPerLetter);
    bits <<= bitClusterCount * bitsPerLetter - bitLength;
    for (let k2 = 1; k2 <= bitClusterCount; k2++) {
      const offset = (bitClusterCount - k2) * bitsPerLetter;
      str += alphabetByValue[(bits & maxLetterValue << offset) >> offset];
    }
    str += "==".slice(0, 4 - bitClusterCount);
  }
  return str;
}
var init_toBase64_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-base64/toBase64.browser.js"() {
    init_fromUtf8_browser();
    init_constants_for_browser();
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-stream/blob/Uint8ArrayBlobAdapter.js
function bindUint8ArrayBlobAdapter(toUtf82, fromUtf84, toBase642, fromBase642) {
  return class Uint8ArrayBlobAdapter2 extends Uint8Array {
    static fromString(source, encoding = "utf-8") {
      if (typeof source === "string") {
        if (encoding === "base64") {
          return Uint8ArrayBlobAdapter2.mutate(fromBase642(source));
        }
        return Uint8ArrayBlobAdapter2.mutate(fromUtf84(source));
      }
      throw new Error(`Unsupported conversion from ${typeof source} to Uint8ArrayBlobAdapter.`);
    }
    static mutate(source) {
      Object.setPrototypeOf(source, Uint8ArrayBlobAdapter2.prototype);
      return source;
    }
    transformToString(encoding = "utf-8") {
      if (encoding === "base64") {
        return toBase642(this);
      }
      return toUtf82(this);
    }
  };
}
var init_Uint8ArrayBlobAdapter = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-stream/blob/Uint8ArrayBlobAdapter.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-utf8/toUtf8.browser.js
var toUtf8;
var init_toUtf8_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-utf8/toUtf8.browser.js"() {
    toUtf8 = (input) => {
      if (typeof input === "string") {
        return input;
      }
      if (typeof input !== "object" || typeof input.byteOffset !== "number" || typeof input.byteLength !== "number") {
        throw new Error("@smithy/util-utf8: toUtf8 encoder function only accepts string | Uint8Array.");
      }
      return new TextDecoder("utf-8").decode(input);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/uuid/v4.js
function bindV4(getRandomValues) {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return () => crypto.randomUUID();
  }
  return () => {
    const rnds = new Uint8Array(16);
    getRandomValues(rnds);
    rnds[6] = rnds[6] & 15 | 64;
    rnds[8] = rnds[8] & 63 | 128;
    return decimalToHex[rnds[0]] + decimalToHex[rnds[1]] + decimalToHex[rnds[2]] + decimalToHex[rnds[3]] + "-" + decimalToHex[rnds[4]] + decimalToHex[rnds[5]] + "-" + decimalToHex[rnds[6]] + decimalToHex[rnds[7]] + "-" + decimalToHex[rnds[8]] + decimalToHex[rnds[9]] + "-" + decimalToHex[rnds[10]] + decimalToHex[rnds[11]] + decimalToHex[rnds[12]] + decimalToHex[rnds[13]] + decimalToHex[rnds[14]] + decimalToHex[rnds[15]];
  };
}
var decimalToHex;
var init_v4 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/uuid/v4.js"() {
    decimalToHex = Array.from({ length: 256 }, (_, i2) => i2.toString(16).padStart(2, "0"));
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/parse-utils.js
var expectNumber, MAX_FLOAT, expectFloat32, expectLong, expectShort, expectByte, expectSizedInt, castInt, strictParseDouble, strictParseFloat32, NUMBER_REGEX, parseNumber, strictParseShort, strictParseByte, stackTraceWarning, logger;
var init_parse_utils = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/parse-utils.js"() {
    expectNumber = (value) => {
      if (value === null || value === void 0) {
        return void 0;
      }
      if (typeof value === "string") {
        const parsed = parseFloat(value);
        if (!Number.isNaN(parsed)) {
          if (String(parsed) !== String(value)) {
            logger.warn(stackTraceWarning(`Expected number but observed string: ${value}`));
          }
          return parsed;
        }
      }
      if (typeof value === "number") {
        return value;
      }
      throw new TypeError(`Expected number, got ${typeof value}: ${value}`);
    };
    MAX_FLOAT = Math.ceil(2 ** 127 * (2 - 2 ** -23));
    expectFloat32 = (value) => {
      const expected = expectNumber(value);
      if (expected !== void 0 && !Number.isNaN(expected) && expected !== Infinity && expected !== -Infinity) {
        if (Math.abs(expected) > MAX_FLOAT) {
          throw new TypeError(`Expected 32-bit float, got ${value}`);
        }
      }
      return expected;
    };
    expectLong = (value) => {
      if (value === null || value === void 0) {
        return void 0;
      }
      if (Number.isInteger(value) && !Number.isNaN(value)) {
        return value;
      }
      throw new TypeError(`Expected integer, got ${typeof value}: ${value}`);
    };
    expectShort = (value) => expectSizedInt(value, 16);
    expectByte = (value) => expectSizedInt(value, 8);
    expectSizedInt = (value, size) => {
      const expected = expectLong(value);
      if (expected !== void 0 && castInt(expected, size) !== expected) {
        throw new TypeError(`Expected ${size}-bit integer, got ${value}`);
      }
      return expected;
    };
    castInt = (value, size) => {
      switch (size) {
        case 32:
          return Int32Array.of(value)[0];
        case 16:
          return Int16Array.of(value)[0];
        case 8:
          return Int8Array.of(value)[0];
      }
    };
    strictParseDouble = (value) => {
      if (typeof value == "string") {
        return expectNumber(parseNumber(value));
      }
      return expectNumber(value);
    };
    strictParseFloat32 = (value) => {
      if (typeof value == "string") {
        return expectFloat32(parseNumber(value));
      }
      return expectFloat32(value);
    };
    NUMBER_REGEX = /(-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)|(-?Infinity)|(NaN)/g;
    parseNumber = (value) => {
      const matches = value.match(NUMBER_REGEX);
      if (matches === null || matches[0].length !== value.length) {
        throw new TypeError(`Expected real number, got implicit NaN`);
      }
      return parseFloat(value);
    };
    strictParseShort = (value) => {
      if (typeof value === "string") {
        return expectShort(parseNumber(value));
      }
      return expectShort(value);
    };
    strictParseByte = (value) => {
      if (typeof value === "string") {
        return expectByte(parseNumber(value));
      }
      return expectByte(value);
    };
    stackTraceWarning = (message) => {
      return String(new TypeError(message).stack || message).split("\n").slice(0, 5).filter((s2) => !s2.includes("stackTraceWarning")).join("\n");
    };
    logger = {
      warn: console.warn
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/date-utils.js
function dateToUtcString(date2) {
  const year2 = date2.getUTCFullYear();
  const month = date2.getUTCMonth();
  const dayOfWeek = date2.getUTCDay();
  const dayOfMonthInt = date2.getUTCDate();
  const hoursInt = date2.getUTCHours();
  const minutesInt = date2.getUTCMinutes();
  const secondsInt = date2.getUTCSeconds();
  const dayOfMonthString = dayOfMonthInt < 10 ? `0${dayOfMonthInt}` : `${dayOfMonthInt}`;
  const hoursString = hoursInt < 10 ? `0${hoursInt}` : `${hoursInt}`;
  const minutesString = minutesInt < 10 ? `0${minutesInt}` : `${minutesInt}`;
  const secondsString = secondsInt < 10 ? `0${secondsInt}` : `${secondsInt}`;
  return `${DAYS[dayOfWeek]}, ${dayOfMonthString} ${MONTHS[month]} ${year2} ${hoursString}:${minutesString}:${secondsString} GMT`;
}
var DAYS, MONTHS, RFC3339, RFC3339_WITH_OFFSET, parseRfc3339DateTimeWithOffset, IMF_FIXDATE, RFC_850_DATE, ASC_TIME, parseRfc7231DateTime, parseEpochTimestamp, buildDate, parseTwoDigitYear, FIFTY_YEARS_IN_MILLIS, adjustRfc850Year, parseMonthByShortName, DAYS_IN_MONTH, validateDayOfMonth, isLeapYear, parseDateValue, parseMilliseconds, parseOffsetToMilliseconds, stripLeadingZeroes;
var init_date_utils = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/date-utils.js"() {
    init_parse_utils();
    DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    RFC3339 = new RegExp(/^(\d{4})-(\d{2})-(\d{2})[tT](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?[zZ]$/);
    RFC3339_WITH_OFFSET = new RegExp(/^(\d{4})-(\d{2})-(\d{2})[tT](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(([-+]\d{2}\:\d{2})|[zZ])$/);
    parseRfc3339DateTimeWithOffset = (value) => {
      if (value === null || value === void 0) {
        return void 0;
      }
      if (typeof value !== "string") {
        throw new TypeError("RFC-3339 date-times must be expressed as strings");
      }
      const match = RFC3339_WITH_OFFSET.exec(value);
      if (!match) {
        throw new TypeError("Invalid RFC-3339 date-time value");
      }
      const [_, yearStr, monthStr, dayStr, hours, minutes, seconds, fractionalMilliseconds, offsetStr] = match;
      const year2 = strictParseShort(stripLeadingZeroes(yearStr));
      const month = parseDateValue(monthStr, "month", 1, 12);
      const day = parseDateValue(dayStr, "day", 1, 31);
      const date2 = buildDate(year2, month, day, { hours, minutes, seconds, fractionalMilliseconds });
      if (offsetStr.toUpperCase() != "Z") {
        date2.setTime(date2.getTime() - parseOffsetToMilliseconds(offsetStr));
      }
      return date2;
    };
    IMF_FIXDATE = new RegExp(/^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\d{2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4}) (\d{1,2}):(\d{2}):(\d{2})(?:\.(\d+))? GMT$/);
    RFC_850_DATE = new RegExp(/^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2}) (\d{1,2}):(\d{2}):(\d{2})(?:\.(\d+))? GMT$/);
    ASC_TIME = new RegExp(/^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) ( [1-9]|\d{2}) (\d{1,2}):(\d{2}):(\d{2})(?:\.(\d+))? (\d{4})$/);
    parseRfc7231DateTime = (value) => {
      if (value === null || value === void 0) {
        return void 0;
      }
      if (typeof value !== "string") {
        throw new TypeError("RFC-7231 date-times must be expressed as strings");
      }
      let match = IMF_FIXDATE.exec(value);
      if (match) {
        const [_, dayStr, monthStr, yearStr, hours, minutes, seconds, fractionalMilliseconds] = match;
        return buildDate(strictParseShort(stripLeadingZeroes(yearStr)), parseMonthByShortName(monthStr), parseDateValue(dayStr, "day", 1, 31), { hours, minutes, seconds, fractionalMilliseconds });
      }
      match = RFC_850_DATE.exec(value);
      if (match) {
        const [_, dayStr, monthStr, yearStr, hours, minutes, seconds, fractionalMilliseconds] = match;
        return adjustRfc850Year(buildDate(parseTwoDigitYear(yearStr), parseMonthByShortName(monthStr), parseDateValue(dayStr, "day", 1, 31), {
          hours,
          minutes,
          seconds,
          fractionalMilliseconds
        }));
      }
      match = ASC_TIME.exec(value);
      if (match) {
        const [_, monthStr, dayStr, hours, minutes, seconds, fractionalMilliseconds, yearStr] = match;
        return buildDate(strictParseShort(stripLeadingZeroes(yearStr)), parseMonthByShortName(monthStr), parseDateValue(dayStr.trimLeft(), "day", 1, 31), { hours, minutes, seconds, fractionalMilliseconds });
      }
      throw new TypeError("Invalid RFC-7231 date-time value");
    };
    parseEpochTimestamp = (value) => {
      if (value === null || value === void 0) {
        return void 0;
      }
      let valueAsDouble;
      if (typeof value === "number") {
        valueAsDouble = value;
      } else if (typeof value === "string") {
        valueAsDouble = strictParseDouble(value);
      } else if (typeof value === "object" && value.tag === 1) {
        valueAsDouble = value.value;
      } else {
        throw new TypeError("Epoch timestamps must be expressed as floating point numbers or their string representation");
      }
      if (Number.isNaN(valueAsDouble) || valueAsDouble === Infinity || valueAsDouble === -Infinity) {
        throw new TypeError("Epoch timestamps must be valid, non-Infinite, non-NaN numerics");
      }
      return new Date(Math.round(valueAsDouble * 1e3));
    };
    buildDate = (year2, month, day, time2) => {
      const adjustedMonth = month - 1;
      validateDayOfMonth(year2, adjustedMonth, day);
      return new Date(Date.UTC(year2, adjustedMonth, day, parseDateValue(time2.hours, "hour", 0, 23), parseDateValue(time2.minutes, "minute", 0, 59), parseDateValue(time2.seconds, "seconds", 0, 60), parseMilliseconds(time2.fractionalMilliseconds)));
    };
    parseTwoDigitYear = (value) => {
      const thisYear = (/* @__PURE__ */ new Date()).getUTCFullYear();
      const valueInThisCentury = Math.floor(thisYear / 100) * 100 + strictParseShort(stripLeadingZeroes(value));
      if (valueInThisCentury < thisYear) {
        return valueInThisCentury + 100;
      }
      return valueInThisCentury;
    };
    FIFTY_YEARS_IN_MILLIS = 50 * 365 * 24 * 60 * 60 * 1e3;
    adjustRfc850Year = (input) => {
      if (input.getTime() - (/* @__PURE__ */ new Date()).getTime() > FIFTY_YEARS_IN_MILLIS) {
        return new Date(Date.UTC(input.getUTCFullYear() - 100, input.getUTCMonth(), input.getUTCDate(), input.getUTCHours(), input.getUTCMinutes(), input.getUTCSeconds(), input.getUTCMilliseconds()));
      }
      return input;
    };
    parseMonthByShortName = (value) => {
      const monthIdx = MONTHS.indexOf(value);
      if (monthIdx < 0) {
        throw new TypeError(`Invalid month: ${value}`);
      }
      return monthIdx + 1;
    };
    DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    validateDayOfMonth = (year2, month, day) => {
      let maxDays = DAYS_IN_MONTH[month];
      if (month === 1 && isLeapYear(year2)) {
        maxDays = 29;
      }
      if (day > maxDays) {
        throw new TypeError(`Invalid day for ${MONTHS[month]} in ${year2}: ${day}`);
      }
    };
    isLeapYear = (year2) => {
      return year2 % 4 === 0 && (year2 % 100 !== 0 || year2 % 400 === 0);
    };
    parseDateValue = (value, type, lower, upper) => {
      const dateVal = strictParseByte(stripLeadingZeroes(value));
      if (dateVal < lower || dateVal > upper) {
        throw new TypeError(`${type} must be between ${lower} and ${upper}, inclusive`);
      }
      return dateVal;
    };
    parseMilliseconds = (value) => {
      if (value === null || value === void 0) {
        return 0;
      }
      return strictParseFloat32("0." + value) * 1e3;
    };
    parseOffsetToMilliseconds = (value) => {
      const directionStr = value[0];
      let direction = 1;
      if (directionStr == "+") {
        direction = 1;
      } else if (directionStr == "-") {
        direction = -1;
      } else {
        throw new TypeError(`Offset direction, ${directionStr}, must be "+" or "-"`);
      }
      const hour = Number(value.substring(1, 3));
      const minute = Number(value.substring(4, 6));
      return direction * (hour * 60 + minute) * 60 * 1e3;
    };
    stripLeadingZeroes = (value) => {
      let idx = 0;
      while (idx < value.length - 1 && value.charAt(idx) === "0") {
        idx++;
      }
      if (idx === 0) {
        return value;
      }
      return value.slice(idx);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/lazy-json.js
var LazyJsonString;
var init_lazy_json = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/lazy-json.js"() {
    LazyJsonString = function LazyJsonString2(val) {
      const str = Object.assign(new String(val), {
        deserializeJSON() {
          return JSON.parse(String(val));
        },
        toString() {
          return String(val);
        },
        toJSON() {
          return String(val);
        }
      });
      return str;
    };
    LazyJsonString.from = (object) => {
      if (object && typeof object === "object" && (object instanceof LazyJsonString || "deserializeJSON" in object)) {
        return object;
      } else if (typeof object === "string" || Object.getPrototypeOf(object) === String.prototype) {
        return LazyJsonString(String(object));
      }
      return LazyJsonString(JSON.stringify(object));
    };
    LazyJsonString.fromObject = LazyJsonString.from;
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/quote-header.js
function quoteHeader(part) {
  if (part.includes(",") || part.includes('"')) {
    part = `"${part.replace(/"/g, '\\"')}"`;
  }
  return part;
}
var init_quote_header = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/quote-header.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/schema-serde-lib/schema-date-utils.js
function range(v2, min, max) {
  const _v2 = Number(v2);
  if (_v2 < min || _v2 > max) {
    throw new Error(`Value ${_v2} out of range [${min}, ${max}]`);
  }
}
var ddd, mmm, time, date, year, RFC3339_WITH_OFFSET2, IMF_FIXDATE2, RFC_850_DATE2, ASC_TIME2, months, _parseEpochTimestamp, _parseRfc3339DateTimeWithOffset, _parseRfc7231DateTime;
var init_schema_date_utils = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/schema-serde-lib/schema-date-utils.js"() {
    ddd = `(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:[ne|u?r]?s?day)?`;
    mmm = `(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)`;
    time = `(\\d?\\d):(\\d{2}):(\\d{2})(?:\\.(\\d+))?`;
    date = `(\\d?\\d)`;
    year = `(\\d{4})`;
    RFC3339_WITH_OFFSET2 = new RegExp(/^(\d{4})-(\d\d)-(\d\d)[tT](\d\d):(\d\d):(\d\d)(\.(\d+))?(([-+]\d\d:\d\d)|[zZ])$/);
    IMF_FIXDATE2 = new RegExp(`^${ddd}, ${date} ${mmm} ${year} ${time} GMT$`);
    RFC_850_DATE2 = new RegExp(`^${ddd}, ${date}-${mmm}-(\\d\\d) ${time} GMT$`);
    ASC_TIME2 = new RegExp(`^${ddd} ${mmm} ( [1-9]|\\d\\d) ${time} ${year}$`);
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    _parseEpochTimestamp = (value) => {
      if (value == null) {
        return void 0;
      }
      let num = NaN;
      if (typeof value === "number") {
        num = value;
      } else if (typeof value === "string") {
        if (!/^-?\d*\.?\d+$/.test(value)) {
          throw new TypeError(`parseEpochTimestamp - numeric string invalid.`);
        }
        num = Number.parseFloat(value);
      } else if (typeof value === "object" && value.tag === 1) {
        num = value.value;
      }
      if (isNaN(num) || Math.abs(num) === Infinity) {
        throw new TypeError("Epoch timestamps must be valid finite numbers.");
      }
      return new Date(Math.round(num * 1e3));
    };
    _parseRfc3339DateTimeWithOffset = (value) => {
      if (value == null) {
        return void 0;
      }
      if (typeof value !== "string") {
        throw new TypeError("RFC3339 timestamps must be strings");
      }
      const matches = RFC3339_WITH_OFFSET2.exec(value);
      if (!matches) {
        throw new TypeError(`Invalid RFC3339 timestamp format ${value}`);
      }
      const [, yearStr, monthStr, dayStr, hours, minutes, seconds, , ms, offsetStr] = matches;
      range(monthStr, 1, 12);
      range(dayStr, 1, 31);
      range(hours, 0, 23);
      range(minutes, 0, 59);
      range(seconds, 0, 60);
      const date2 = new Date(Date.UTC(Number(yearStr), Number(monthStr) - 1, Number(dayStr), Number(hours), Number(minutes), Number(seconds), Number(ms) ? Math.round(parseFloat(`0.${ms}`) * 1e3) : 0));
      date2.setUTCFullYear(Number(yearStr));
      if (offsetStr.toUpperCase() != "Z") {
        const [, sign, offsetH, offsetM] = /([+-])(\d\d):(\d\d)/.exec(offsetStr) || [void 0, "+", 0, 0];
        const scalar = sign === "-" ? 1 : -1;
        date2.setTime(date2.getTime() + scalar * (Number(offsetH) * 60 * 60 * 1e3 + Number(offsetM) * 60 * 1e3));
      }
      return date2;
    };
    _parseRfc7231DateTime = (value) => {
      if (value == null) {
        return void 0;
      }
      if (typeof value !== "string") {
        throw new TypeError("RFC7231 timestamps must be strings.");
      }
      let day;
      let month;
      let year2;
      let hour;
      let minute;
      let second;
      let fraction;
      let matches;
      if (matches = IMF_FIXDATE2.exec(value)) {
        [, day, month, year2, hour, minute, second, fraction] = matches;
      } else if (matches = RFC_850_DATE2.exec(value)) {
        [, day, month, year2, hour, minute, second, fraction] = matches;
        year2 = (Number(year2) + 1900).toString();
      } else if (matches = ASC_TIME2.exec(value)) {
        [, month, day, hour, minute, second, fraction, year2] = matches;
      }
      if (year2 && second) {
        const timestamp = Date.UTC(Number(year2), months.indexOf(month), Number(day), Number(hour), Number(minute), Number(second), fraction ? Math.round(parseFloat(`0.${fraction}`) * 1e3) : 0);
        range(day, 1, 31);
        range(hour, 0, 23);
        range(minute, 0, 59);
        range(second, 0, 60);
        const date2 = new Date(timestamp);
        date2.setUTCFullYear(Number(year2));
        return date2;
      }
      throw new TypeError(`Invalid RFC7231 date-time value ${value}.`);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/split-every.js
function splitEvery(value, delimiter, numDelimiters) {
  if (numDelimiters <= 0 || !Number.isInteger(numDelimiters)) {
    throw new Error("Invalid number of delimiters (" + numDelimiters + ") for splitEvery.");
  }
  const segments = value.split(delimiter);
  if (numDelimiters === 1) {
    return segments;
  }
  const compoundSegments = [];
  let currentSegment = "";
  for (let i2 = 0; i2 < segments.length; i2++) {
    if (currentSegment === "") {
      currentSegment = segments[i2];
    } else {
      currentSegment += delimiter + segments[i2];
    }
    if ((i2 + 1) % numDelimiters === 0) {
      compoundSegments.push(currentSegment);
      currentSegment = "";
    }
  }
  if (currentSegment !== "") {
    compoundSegments.push(currentSegment);
  }
  return compoundSegments;
}
var init_split_every = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/split-every.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/split-header.js
var splitHeader;
var init_split_header = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/split-header.js"() {
    splitHeader = (value) => {
      const z = value.length;
      const values = [];
      let withinQuotes = false;
      let prevChar = void 0;
      let anchor = 0;
      for (let i2 = 0; i2 < z; ++i2) {
        const char = value[i2];
        switch (char) {
          case `"`:
            if (prevChar !== "\\") {
              withinQuotes = !withinQuotes;
            }
            break;
          case ",":
            if (!withinQuotes) {
              values.push(value.slice(anchor, i2));
              anchor = i2 + 1;
            }
            break;
          default:
        }
        prevChar = char;
      }
      values.push(value.slice(anchor));
      return values.map((v2) => {
        v2 = v2.trim();
        const z2 = v2.length;
        if (z2 < 2) {
          return v2;
        }
        if (v2[0] === `"` && v2[z2 - 1] === `"`) {
          v2 = v2.slice(1, z2 - 1);
        }
        return v2.replace(/\\"/g, '"');
      });
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/value/NumericValue.js
var format, NumericValue;
var init_NumericValue = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/value/NumericValue.js"() {
    format = /^-?\d*(\.\d+)?$/;
    NumericValue = class _NumericValue {
      string;
      type;
      constructor(string, type) {
        this.string = string;
        this.type = type;
        if (!format.test(string)) {
          throw new Error(`@smithy/core/serde - NumericValue must only contain [0-9], at most one decimal point ".", and an optional negation prefix "-".`);
        }
      }
      toString() {
        return this.string;
      }
      static [Symbol.hasInstance](object) {
        if (!object || typeof object !== "object") {
          return false;
        }
        const _nv = object;
        return _NumericValue.prototype.isPrototypeOf(object) || _nv.type === "bigDecimal" && format.test(_nv.string);
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-hex-encoding/hex-encoding.js
function fromHex(encoded) {
  if (encoded.length % 2 !== 0) {
    throw new Error("Hex encoded strings must have an even number length");
  }
  const out = new Uint8Array(encoded.length / 2);
  for (let i2 = 0; i2 < encoded.length; i2 += 2) {
    const encodedByte = encoded.slice(i2, i2 + 2).toLowerCase();
    if (encodedByte in HEX_TO_SHORT) {
      out[i2 / 2] = HEX_TO_SHORT[encodedByte];
    } else {
      throw new Error(`Cannot decode unrecognized sequence ${encodedByte} as hexadecimal`);
    }
  }
  return out;
}
function toHex(bytes) {
  let out = "";
  for (let i2 = 0; i2 < bytes.byteLength; i2++) {
    out += SHORT_TO_HEX[bytes[i2]];
  }
  return out;
}
var SHORT_TO_HEX, HEX_TO_SHORT;
var init_hex_encoding = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-hex-encoding/hex-encoding.js"() {
    SHORT_TO_HEX = {};
    HEX_TO_SHORT = {};
    for (let i2 = 0; i2 < 256; i2++) {
      let encodedByte = i2.toString(16).toLowerCase();
      if (encodedByte.length === 1) {
        encodedByte = `0${encodedByte}`;
      }
      SHORT_TO_HEX[i2] = encodedByte;
      HEX_TO_SHORT[encodedByte] = i2;
    }
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-body-length/calculateBodyLength.browser.js
var TEXT_ENCODER, calculateBodyLength;
var init_calculateBodyLength_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-body-length/calculateBodyLength.browser.js"() {
    TEXT_ENCODER = typeof TextEncoder == "function" ? new TextEncoder() : null;
    calculateBodyLength = (body) => {
      if (typeof body === "string") {
        if (TEXT_ENCODER) {
          return TEXT_ENCODER.encode(body).byteLength;
        }
        let len = body.length;
        for (let i2 = len - 1; i2 >= 0; i2--) {
          const code = body.charCodeAt(i2);
          if (code > 127 && code <= 2047)
            len++;
          else if (code > 2047 && code <= 65535)
            len += 2;
          if (code >= 56320 && code <= 57343)
            i2--;
        }
        return len;
      } else if (typeof body.byteLength === "number") {
        return body.byteLength;
      } else if (typeof body.size === "number") {
        return body.size;
      }
      throw new Error(`Body Length computation failed for ${body}`);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-utf8/toUint8Array.browser.js
var toUint8Array;
var init_toUint8Array_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-utf8/toUint8Array.browser.js"() {
    init_fromUtf8_browser();
    toUint8Array = (data) => {
      if (data instanceof Uint8Array) {
        return data;
      }
      if (typeof data === "string") {
        return fromUtf8(data);
      }
      if (ArrayBuffer.isView(data)) {
        return new Uint8Array(data.buffer, data.byteOffset, data.byteLength / Uint8Array.BYTES_PER_ELEMENT);
      }
      return new Uint8Array(data);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/concatBytes.js
function concatBytes(arrays, length) {
  if (length === void 0) {
    length = 0;
    for (const bytes of arrays) {
      length += bytes.byteLength;
    }
  }
  const result = new Uint8Array(length);
  let offset = 0;
  for (const buf of arrays) {
    result.set(buf, offset);
    offset += buf.byteLength;
  }
  return result;
}
var init_concatBytes = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/concatBytes.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/is-array-buffer/is-array-buffer.js
var isArrayBuffer;
var init_is_array_buffer = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/is-array-buffer/is-array-buffer.js"() {
    isArrayBuffer = (arg) => typeof ArrayBuffer === "function" && arg instanceof ArrayBuffer || Object.prototype.toString.call(arg) === "[object ArrayBuffer]";
  }
});

// node_modules/@smithy/types/dist-es/endpoint.js
var EndpointURLScheme;
var init_endpoint = __esm({
  "node_modules/@smithy/types/dist-es/endpoint.js"() {
    (function(EndpointURLScheme2) {
      EndpointURLScheme2["HTTP"] = "http";
      EndpointURLScheme2["HTTPS"] = "https";
    })(EndpointURLScheme || (EndpointURLScheme = {}));
  }
});

// node_modules/@smithy/types/dist-es/extensions/checksum.js
var AlgorithmId;
var init_checksum = __esm({
  "node_modules/@smithy/types/dist-es/extensions/checksum.js"() {
    (function(AlgorithmId2) {
      AlgorithmId2["MD5"] = "md5";
      AlgorithmId2["CRC32"] = "crc32";
      AlgorithmId2["CRC32C"] = "crc32c";
      AlgorithmId2["SHA1"] = "sha1";
      AlgorithmId2["SHA256"] = "sha256";
    })(AlgorithmId || (AlgorithmId = {}));
  }
});

// node_modules/@smithy/types/dist-es/extensions/index.js
var init_extensions = __esm({
  "node_modules/@smithy/types/dist-es/extensions/index.js"() {
    init_checksum();
  }
});

// node_modules/@smithy/types/dist-es/middleware.js
var SMITHY_CONTEXT_KEY;
var init_middleware = __esm({
  "node_modules/@smithy/types/dist-es/middleware.js"() {
    SMITHY_CONTEXT_KEY = "__smithy_context";
  }
});

// node_modules/@smithy/types/dist-es/index.js
var init_dist_es = __esm({
  "node_modules/@smithy/types/dist-es/index.js"() {
    init_endpoint();
    init_extensions();
    init_middleware();
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/getSmithyContext.js
var getSmithyContext;
var init_getSmithyContext = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/getSmithyContext.js"() {
    init_dist_es();
    getSmithyContext = (context) => context[SMITHY_CONTEXT_KEY] || (context[SMITHY_CONTEXT_KEY] = {});
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/httpRequest.js
function cloneQuery(query) {
  return Object.keys(query).reduce((carry, paramName) => {
    const param = query[paramName];
    return {
      ...carry,
      [paramName]: Array.isArray(param) ? [...param] : param
    };
  }, {});
}
var HttpRequest;
var init_httpRequest = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/httpRequest.js"() {
    HttpRequest = class _HttpRequest {
      method;
      protocol;
      hostname;
      port;
      path;
      query;
      headers;
      username;
      password;
      fragment;
      body;
      constructor(options) {
        this.method = options.method || "GET";
        this.hostname = options.hostname || "localhost";
        this.port = options.port;
        this.query = options.query || {};
        this.headers = options.headers || {};
        this.body = options.body;
        this.protocol = options.protocol ? options.protocol.slice(-1) !== ":" ? `${options.protocol}:` : options.protocol : "https:";
        this.path = options.path ? options.path.charAt(0) !== "/" ? `/${options.path}` : options.path : "/";
        this.username = options.username;
        this.password = options.password;
        this.fragment = options.fragment;
      }
      static clone(request) {
        const cloned = new _HttpRequest({
          ...request,
          headers: { ...request.headers }
        });
        if (cloned.query) {
          cloned.query = cloneQuery(cloned.query);
        }
        return cloned;
      }
      static isInstance(request) {
        if (!request) {
          return false;
        }
        const req = request;
        return "method" in req && "protocol" in req && "hostname" in req && "path" in req && typeof req["query"] === "object" && typeof req["headers"] === "object";
      }
      clone() {
        return _HttpRequest.clone(this);
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/httpResponse.js
var HttpResponse;
var init_httpResponse = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/httpResponse.js"() {
    HttpResponse = class {
      statusCode;
      reason;
      headers;
      body;
      constructor(options) {
        this.statusCode = options.statusCode;
        this.reason = options.reason;
        this.headers = options.headers || {};
        this.body = options.body;
      }
      static isInstance(response) {
        if (!response)
          return false;
        const resp = response;
        return typeof resp.statusCode === "number" && typeof resp.headers === "object";
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/isValidHostLabel.js
var VALID_HOST_LABEL_REGEX, isValidHostLabel;
var init_isValidHostLabel = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/isValidHostLabel.js"() {
    VALID_HOST_LABEL_REGEX = new RegExp(`^(?!.*-$)(?!-)[a-zA-Z0-9-]{1,63}$`);
    isValidHostLabel = (value, allowSubDomains = false) => {
      if (!allowSubDomains) {
        return VALID_HOST_LABEL_REGEX.test(value);
      }
      const labels = value.split(".");
      for (const label of labels) {
        if (!isValidHostLabel(label)) {
          return false;
        }
      }
      return true;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/isValidHostname.js
function isValidHostname(hostname) {
  const hostPattern = /^[a-z0-9][a-z0-9\.\-]*[a-z0-9]$/;
  return hostPattern.test(hostname);
}
var init_isValidHostname = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/isValidHostname.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/normalizeProvider.js
var normalizeProvider;
var init_normalizeProvider = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/normalizeProvider.js"() {
    normalizeProvider = (input) => {
      if (typeof input === "function")
        return input;
      const promisified = Promise.resolve(input);
      return () => promisified;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/parseQueryString.js
function parseQueryString(querystring) {
  const query = {};
  querystring = querystring.replace(/^\?/, "");
  if (querystring) {
    for (const pair of querystring.split("&")) {
      let [key, value = null] = pair.split("=");
      key = decodeURIComponent(key);
      if (value) {
        value = decodeURIComponent(value);
      }
      if (!(key in query)) {
        query[key] = value;
      } else if (Array.isArray(query[key])) {
        query[key].push(value);
      } else {
        query[key] = [query[key], value];
      }
    }
  }
  return query;
}
var init_parseQueryString = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/parseQueryString.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/parseUrl.js
var parseUrl;
var init_parseUrl = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/parseUrl.js"() {
    init_parseQueryString();
    parseUrl = (url) => {
      if (typeof url === "string") {
        return parseUrl(new URL(url));
      }
      const { hostname, pathname, port, protocol, search } = url;
      let query;
      if (search) {
        query = parseQueryString(search);
      }
      return {
        hostname,
        port: port ? parseInt(port) : void 0,
        protocol,
        path: pathname,
        query
      };
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/toEndpointV1.js
var toEndpointV1;
var init_toEndpointV1 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/toEndpointV1.js"() {
    init_parseUrl();
    toEndpointV1 = (endpoint) => {
      if (typeof endpoint === "object") {
        if ("url" in endpoint) {
          const v1Endpoint = parseUrl(endpoint.url);
          if (endpoint.headers) {
            v1Endpoint.headers = {};
            for (const name in endpoint.headers) {
              v1Endpoint.headers[name.toLowerCase()] = endpoint.headers[name].join(", ");
            }
          }
          return v1Endpoint;
        }
        return endpoint;
      }
      return parseUrl(endpoint);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/transport/index.js
var init_transport = __esm({
  "node_modules/@smithy/core/dist-es/submodules/transport/index.js"() {
    init_getSmithyContext();
    init_httpRequest();
    init_httpResponse();
    init_isValidHostLabel();
    init_isValidHostname();
    init_normalizeProvider();
    init_parseUrl();
    init_toEndpointV1();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/getEndpointFromConfig.browser.js
var getEndpointFromConfig;
var init_getEndpointFromConfig_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/getEndpointFromConfig.browser.js"() {
    getEndpointFromConfig = async (serviceId) => void 0;
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/service-customizations/s3.js
var resolveParamsForS3, DOMAIN_PATTERN, IP_ADDRESS_PATTERN, DOTS_PATTERN, isDnsCompatibleBucketName, isArnBucketName;
var init_s3 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/service-customizations/s3.js"() {
    resolveParamsForS3 = async (endpointParams) => {
      const bucket = endpointParams?.Bucket || "";
      if (typeof endpointParams.Bucket === "string") {
        endpointParams.Bucket = bucket.replace(/#/g, encodeURIComponent("#")).replace(/\?/g, encodeURIComponent("?"));
      }
      if (isArnBucketName(bucket)) {
        if (endpointParams.ForcePathStyle === true) {
          throw new Error("Path-style addressing cannot be used with ARN buckets");
        }
      } else if (!isDnsCompatibleBucketName(bucket) || bucket.indexOf(".") !== -1 && !String(endpointParams.Endpoint).startsWith("http:") || bucket.toLowerCase() !== bucket || bucket.length < 3) {
        endpointParams.ForcePathStyle = true;
      }
      if (endpointParams.DisableMultiRegionAccessPoints) {
        endpointParams.disableMultiRegionAccessPoints = true;
        endpointParams.DisableMRAP = true;
      }
      return endpointParams;
    };
    DOMAIN_PATTERN = /^[a-z0-9][a-z0-9\.\-]{1,61}[a-z0-9]$/;
    IP_ADDRESS_PATTERN = /(\d+\.){3}\d+/;
    DOTS_PATTERN = /\.\./;
    isDnsCompatibleBucketName = (bucketName) => DOMAIN_PATTERN.test(bucketName) && !IP_ADDRESS_PATTERN.test(bucketName) && !DOTS_PATTERN.test(bucketName);
    isArnBucketName = (bucketName) => {
      const [arn, partition2, service, , , bucket] = bucketName.split(":");
      const isArn = arn === "arn" && bucketName.split(":").length >= 6;
      const isValidArn = Boolean(isArn && partition2 && service && bucket);
      if (isArn && !isValidArn) {
        throw new Error(`Invalid ARN: ${bucketName} was an invalid ARN.`);
      }
      return isValidArn;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/service-customizations/index.js
var init_service_customizations = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/service-customizations/index.js"() {
    init_s3();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/createConfigValueProvider.js
var createConfigValueProvider;
var init_createConfigValueProvider = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/createConfigValueProvider.js"() {
    createConfigValueProvider = (configKey, canonicalEndpointParamKey, config, isClientContextParam = false) => {
      const configProvider = async () => {
        let configValue;
        if (isClientContextParam) {
          const clientContextParams = config.clientContextParams;
          const nestedValue = clientContextParams?.[configKey];
          configValue = nestedValue ?? config[configKey] ?? config[canonicalEndpointParamKey];
        } else {
          configValue = config[configKey] ?? config[canonicalEndpointParamKey];
        }
        if (typeof configValue === "function") {
          return configValue();
        }
        return configValue;
      };
      if (configKey === "credentialScope" || canonicalEndpointParamKey === "CredentialScope") {
        return async () => {
          const credentials = typeof config.credentials === "function" ? await config.credentials() : config.credentials;
          const configValue = credentials?.credentialScope ?? credentials?.CredentialScope;
          return configValue;
        };
      }
      if (configKey === "accountId" || canonicalEndpointParamKey === "AccountId") {
        return async () => {
          const credentials = typeof config.credentials === "function" ? await config.credentials() : config.credentials;
          const configValue = credentials?.accountId ?? credentials?.AccountId;
          return configValue;
        };
      }
      if (configKey === "endpoint" || canonicalEndpointParamKey === "endpoint") {
        return async () => {
          if (config.isCustomEndpoint === false) {
            return void 0;
          }
          const endpoint = await configProvider();
          if (endpoint && typeof endpoint === "object") {
            if ("url" in endpoint) {
              return endpoint.url.href;
            }
            if ("hostname" in endpoint) {
              const { protocol, hostname, port, path } = endpoint;
              return `${protocol}//${hostname}${port ? ":" + port : ""}${path}`;
            }
          }
          return endpoint;
        };
      }
      return configProvider;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/toEndpointV1.js
var init_toEndpointV12 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/toEndpointV1.js"() {
    init_transport();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/getEndpointFromInstructions.js
function bindGetEndpointFromInstructions(getEndpointFromConfig2) {
  return async (commandInput, instructionsSupplier, clientConfig, context) => {
    if (!clientConfig.isCustomEndpoint) {
      let endpointFromConfig;
      if (clientConfig.serviceConfiguredEndpoint) {
        endpointFromConfig = await clientConfig.serviceConfiguredEndpoint();
      } else {
        endpointFromConfig = await getEndpointFromConfig2(clientConfig.serviceId);
      }
      if (endpointFromConfig) {
        clientConfig.endpoint = () => Promise.resolve(toEndpointV1(endpointFromConfig));
        clientConfig.isCustomEndpoint = true;
      }
    }
    const endpointParams = await resolveParams(commandInput, instructionsSupplier, clientConfig);
    if (typeof clientConfig.endpointProvider !== "function") {
      throw new Error("config.endpointProvider is not set.");
    }
    const endpoint = clientConfig.endpointProvider(endpointParams, context);
    if (clientConfig.isCustomEndpoint && clientConfig.endpoint) {
      const customEndpoint = await clientConfig.endpoint();
      if (customEndpoint?.headers) {
        endpoint.headers ??= {};
        for (const [name, value] of Object.entries(customEndpoint.headers)) {
          endpoint.headers[name] = Array.isArray(value) ? value : [value];
        }
      }
    }
    return endpoint;
  };
}
var resolveParams;
var init_getEndpointFromInstructions = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/adaptors/getEndpointFromInstructions.js"() {
    init_service_customizations();
    init_createConfigValueProvider();
    init_toEndpointV12();
    resolveParams = async (commandInput, instructionsSupplier, clientConfig) => {
      const endpointParams = {};
      const instructions = instructionsSupplier?.getEndpointParameterInstructions?.() || {};
      for (const [name, instruction] of Object.entries(instructions)) {
        switch (instruction.type) {
          case "staticContextParams":
            endpointParams[name] = instruction.value;
            break;
          case "contextParams":
            endpointParams[name] = commandInput[instruction.name];
            break;
          case "clientContextParams":
          case "builtInParams":
            endpointParams[name] = await createConfigValueProvider(instruction.name, name, clientConfig, instruction.type !== "builtInParams")();
            break;
          case "operationContextParams":
            endpointParams[name] = instruction.get(commandInput);
            break;
          default:
            throw new Error("Unrecognized endpoint parameter instruction: " + JSON.stringify(instruction));
        }
      }
      if (Object.keys(instructions).length === 0) {
        Object.assign(endpointParams, clientConfig);
      }
      if (String(clientConfig.serviceId).toLowerCase() === "s3") {
        await resolveParamsForS3(endpointParams);
      }
      return endpointParams;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/endpointMiddleware.js
function setFeature(context, feature, value) {
  if (!context.__smithy_context) {
    context.__smithy_context = { features: {} };
  } else if (!context.__smithy_context.features) {
    context.__smithy_context.features = {};
  }
  context.__smithy_context.features[feature] = value;
}
function bindEndpointMiddleware(getEndpointFromConfig2) {
  const getEndpointFromInstructions2 = bindGetEndpointFromInstructions(getEndpointFromConfig2);
  return ({ config, instructions }) => {
    return (next, context) => async (args) => {
      if (config.isCustomEndpoint) {
        setFeature(context, "ENDPOINT_OVERRIDE", "N");
      }
      const endpoint = await getEndpointFromInstructions2(args.input, {
        getEndpointParameterInstructions() {
          return instructions;
        }
      }, { ...config }, context);
      context.endpointV2 = endpoint;
      context.authSchemes = endpoint.properties?.authSchemes;
      const authScheme = context.authSchemes?.[0];
      if (authScheme) {
        context["signing_region"] = authScheme.signingRegion;
        context["signing_service"] = authScheme.signingName;
        const smithyContext = getSmithyContext(context);
        const httpAuthOption = smithyContext?.selectedHttpAuthScheme?.httpAuthOption;
        if (httpAuthOption) {
          httpAuthOption.signingProperties = Object.assign(httpAuthOption.signingProperties || {}, {
            signing_region: authScheme.signingRegion,
            signingRegion: authScheme.signingRegion,
            signing_service: authScheme.signingName,
            signingName: authScheme.signingName,
            signingRegionSet: authScheme.signingRegionSet
          }, authScheme.properties);
        }
      }
      return next({
        ...args
      });
    };
  };
}
var init_endpointMiddleware = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/endpointMiddleware.js"() {
    init_transport();
    init_getEndpointFromInstructions();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/getEndpointPlugin.js
function bindGetEndpointPlugin(getEndpointFromConfig2) {
  const endpointMiddleware2 = bindEndpointMiddleware(getEndpointFromConfig2);
  return (config, instructions) => ({
    applyToStack: (clientStack) => {
      clientStack.addRelativeTo(endpointMiddleware2({
        config,
        instructions
      }), endpointMiddlewareOptions);
    }
  });
}
var serializerMiddlewareOption, endpointMiddlewareOptions;
var init_getEndpointPlugin = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/getEndpointPlugin.js"() {
    init_endpointMiddleware();
    serializerMiddlewareOption = {
      name: "serializerMiddleware",
      step: "serialize",
      tags: ["SERIALIZER"],
      override: true
    };
    endpointMiddlewareOptions = {
      step: "serialize",
      tags: ["ENDPOINT_PARAMETERS", "ENDPOINT_V2", "ENDPOINT"],
      name: "endpointV2Middleware",
      override: true,
      relation: "before",
      toMiddleware: serializerMiddlewareOption.name
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/resolveEndpointConfig.js
function bindResolveEndpointConfig(getEndpointFromConfig2) {
  return (input) => {
    const tls = input.tls ?? true;
    const { endpoint, useDualstackEndpoint, useFipsEndpoint } = input;
    const customEndpointProvider = endpoint != null ? async () => toEndpointV1(await normalizeProvider(endpoint)()) : void 0;
    const isCustomEndpoint = !!endpoint;
    const resolvedConfig = Object.assign(input, {
      endpoint: customEndpointProvider,
      tls,
      isCustomEndpoint,
      useDualstackEndpoint: normalizeProvider(useDualstackEndpoint ?? false),
      useFipsEndpoint: normalizeProvider(useFipsEndpoint ?? false)
    });
    let configuredEndpointPromise = void 0;
    resolvedConfig.serviceConfiguredEndpoint = async () => {
      if (input.serviceId && !configuredEndpointPromise) {
        configuredEndpointPromise = getEndpointFromConfig2(input.serviceId);
      }
      return configuredEndpointPromise;
    };
    return resolvedConfig;
  };
}
var init_resolveEndpointConfig = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/middleware-endpoint/resolveEndpointConfig.js"() {
    init_transport();
    init_toEndpointV12();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/cache/EndpointCache.js
var EndpointCache;
var init_EndpointCache = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/cache/EndpointCache.js"() {
    EndpointCache = class {
      capacity;
      data = /* @__PURE__ */ new Map();
      parameters = [];
      constructor({ size, params }) {
        this.capacity = size ?? 50;
        if (params) {
          this.parameters = params;
        }
      }
      get(endpointParams, resolver) {
        const key = this.hash(endpointParams);
        if (key === false) {
          return resolver();
        }
        if (!this.data.has(key)) {
          if (this.data.size > this.capacity + 10) {
            const keys = this.data.keys();
            let i2 = 0;
            while (true) {
              const { value, done } = keys.next();
              this.data.delete(value);
              if (done || ++i2 > 10) {
                break;
              }
            }
          }
          this.data.set(key, resolver());
        }
        return this.data.get(key);
      }
      size() {
        return this.data.size;
      }
      hash(endpointParams) {
        let buffer = "";
        const { parameters } = this;
        if (parameters.length === 0) {
          return false;
        }
        for (const param of parameters) {
          const val = String(endpointParams[param] ?? "");
          if (val.includes("|;")) {
            return false;
          }
          buffer += val + "|;";
        }
        return buffer;
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/types/EndpointError.js
var EndpointError;
var init_EndpointError = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/types/EndpointError.js"() {
    EndpointError = class extends Error {
      constructor(message) {
        super(message);
        this.name = "EndpointError";
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/types/index.js
var init_types = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/types/index.js"() {
    init_EndpointError();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/debug/debugId.js
var debugId;
var init_debugId = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/debug/debugId.js"() {
    debugId = "endpoints";
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/debug/toDebugString.js
function toDebugString(input) {
  if (typeof input !== "object" || input == null) {
    return input;
  }
  if ("ref" in input) {
    return `$${toDebugString(input.ref)}`;
  }
  if ("fn" in input) {
    return `${input.fn}(${(input.argv || []).map(toDebugString).join(", ")})`;
  }
  return JSON.stringify(input, null, 2);
}
var init_toDebugString = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/debug/toDebugString.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/debug/index.js
var init_debug = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/debug/index.js"() {
    init_debugId();
    init_toDebugString();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/customEndpointFunctions.js
var customEndpointFunctions;
var init_customEndpointFunctions = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/customEndpointFunctions.js"() {
    customEndpointFunctions = {};
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/booleanEquals.js
var booleanEquals;
var init_booleanEquals = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/booleanEquals.js"() {
    booleanEquals = (value1, value2) => value1 === value2;
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/coalesce.js
function coalesce(...args) {
  for (const arg of args) {
    if (arg != null) {
      return arg;
    }
  }
  return void 0;
}
var init_coalesce = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/coalesce.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/getAttrPathList.js
var getAttrPathList;
var init_getAttrPathList = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/getAttrPathList.js"() {
    init_types();
    getAttrPathList = (path) => {
      const parts = path.split(".");
      const pathList = [];
      for (const part of parts) {
        const squareBracketIndex = part.indexOf("[");
        if (squareBracketIndex !== -1) {
          if (part.indexOf("]") !== part.length - 1) {
            throw new EndpointError(`Path: '${path}' does not end with ']'`);
          }
          const arrayIndex = part.slice(squareBracketIndex + 1, -1);
          if (Number.isNaN(parseInt(arrayIndex))) {
            throw new EndpointError(`Invalid array index: '${arrayIndex}' in path: '${path}'`);
          }
          if (squareBracketIndex !== 0) {
            pathList.push(part.slice(0, squareBracketIndex));
          }
          pathList.push(arrayIndex);
        } else {
          pathList.push(part);
        }
      }
      return pathList;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/getAttr.js
var getAttr;
var init_getAttr = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/getAttr.js"() {
    init_types();
    init_getAttrPathList();
    getAttr = (value, path) => getAttrPathList(path).reduce((acc, index) => {
      if (typeof acc !== "object") {
        throw new EndpointError(`Index '${index}' in '${path}' not found in '${JSON.stringify(value)}'`);
      } else if (Array.isArray(acc)) {
        const i2 = parseInt(index);
        return acc[i2 < 0 ? acc.length + i2 : i2];
      }
      return acc[index];
    }, value);
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/isSet.js
var isSet;
var init_isSet = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/isSet.js"() {
    isSet = (value) => value != null;
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/ite.js
function ite(condition, trueValue, falseValue) {
  return condition ? trueValue : falseValue;
}
var init_ite = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/ite.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/not.js
var not;
var init_not = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/not.js"() {
    not = (value) => !value;
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/isIpAddress.js
var IP_V4_REGEX, isIpAddress;
var init_isIpAddress = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/isIpAddress.js"() {
    IP_V4_REGEX = new RegExp(`^(?:25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]\\d|\\d)(?:\\.(?:25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]\\d|\\d)){3}$`);
    isIpAddress = (value) => IP_V4_REGEX.test(value) || value.startsWith("[") && value.endsWith("]");
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/parseURL.js
var DEFAULT_PORTS, parseURL;
var init_parseURL = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/parseURL.js"() {
    init_dist_es();
    init_isIpAddress();
    DEFAULT_PORTS = {
      [EndpointURLScheme.HTTP]: 80,
      [EndpointURLScheme.HTTPS]: 443
    };
    parseURL = (value) => {
      const whatwgURL = (() => {
        try {
          if (value instanceof URL) {
            return value;
          }
          if (typeof value === "object" && "hostname" in value) {
            const { hostname: hostname2, port, protocol: protocol2 = "", path = "", query = {} } = value;
            const url = new URL(`${protocol2}//${hostname2}${port ? `:${port}` : ""}${path}`);
            url.search = Object.entries(query).map(([k2, v2]) => `${k2}=${v2}`).join("&");
            return url;
          }
          return new URL(value);
        } catch (error) {
          return null;
        }
      })();
      if (!whatwgURL) {
        console.error(`Unable to parse ${JSON.stringify(value)} as a whatwg URL.`);
        return null;
      }
      const urlString = whatwgURL.href;
      const { host, hostname, pathname, protocol, search } = whatwgURL;
      if (search) {
        return null;
      }
      const scheme = protocol.slice(0, -1);
      if (!Object.values(EndpointURLScheme).includes(scheme)) {
        return null;
      }
      const isIp = isIpAddress(hostname);
      const inputContainsDefaultPort = urlString.includes(`${host}:${DEFAULT_PORTS[scheme]}`) || typeof value === "string" && value.includes(`${host}:${DEFAULT_PORTS[scheme]}`);
      const authority = `${host}${inputContainsDefaultPort ? `:${DEFAULT_PORTS[scheme]}` : ``}`;
      return {
        scheme,
        authority,
        path: pathname,
        normalizedPath: pathname.endsWith("/") ? pathname : `${pathname}/`,
        isIp
      };
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/split.js
function split(value, delimiter, limit) {
  if (limit === 1) {
    return [value];
  }
  if (value === "") {
    return [""];
  }
  const parts = value.split(delimiter);
  if (limit === 0) {
    return parts;
  }
  return parts.slice(0, limit - 1).concat(parts.slice(1).join(delimiter));
}
var init_split = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/split.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/stringEquals.js
var stringEquals;
var init_stringEquals = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/stringEquals.js"() {
    stringEquals = (value1, value2) => value1 === value2;
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/substring.js
var substring;
var init_substring = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/substring.js"() {
    substring = (input, start, stop, reverse) => {
      if (input == null || start >= stop || input.length < stop || /[^\u0000-\u007f]/.test(input)) {
        return null;
      }
      if (!reverse) {
        return input.substring(start, stop);
      }
      return input.substring(input.length - stop, input.length - start);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/uriEncode.js
var uriEncode;
var init_uriEncode = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/uriEncode.js"() {
    uriEncode = (value) => encodeURIComponent(value).replace(/[!*'()]/g, (c2) => `%${c2.charCodeAt(0).toString(16).toUpperCase()}`);
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/index.js
var init_lib = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/lib/index.js"() {
    init_booleanEquals();
    init_coalesce();
    init_getAttr();
    init_isSet();
    init_transport();
    init_ite();
    init_not();
    init_parseURL();
    init_split();
    init_stringEquals();
    init_substring();
    init_uriEncode();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/endpointFunctions.js
var endpointFunctions;
var init_endpointFunctions = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/endpointFunctions.js"() {
    init_lib();
    endpointFunctions = {
      booleanEquals,
      coalesce,
      getAttr,
      isSet,
      isValidHostLabel,
      ite,
      not,
      parseURL,
      split,
      stringEquals,
      substring,
      uriEncode
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateTemplate.js
var evaluateTemplate;
var init_evaluateTemplate = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateTemplate.js"() {
    init_lib();
    evaluateTemplate = (template, options) => {
      const evaluatedTemplateArr = [];
      const { referenceRecord, endpointParams } = options;
      let currentIndex = 0;
      while (currentIndex < template.length) {
        const openingBraceIndex = template.indexOf("{", currentIndex);
        if (openingBraceIndex === -1) {
          evaluatedTemplateArr.push(template.slice(currentIndex));
          break;
        }
        evaluatedTemplateArr.push(template.slice(currentIndex, openingBraceIndex));
        const closingBraceIndex = template.indexOf("}", openingBraceIndex);
        if (closingBraceIndex === -1) {
          evaluatedTemplateArr.push(template.slice(openingBraceIndex));
          break;
        }
        if (template[openingBraceIndex + 1] === "{" && template[closingBraceIndex + 1] === "}") {
          evaluatedTemplateArr.push(template.slice(openingBraceIndex + 1, closingBraceIndex));
          currentIndex = closingBraceIndex + 2;
        }
        const parameterName = template.substring(openingBraceIndex + 1, closingBraceIndex);
        if (parameterName.includes("#")) {
          const [refName, attrName] = parameterName.split("#");
          evaluatedTemplateArr.push(getAttr(referenceRecord[refName] ?? endpointParams[refName], attrName));
        } else {
          evaluatedTemplateArr.push(referenceRecord[parameterName] ?? endpointParams[parameterName]);
        }
        currentIndex = closingBraceIndex + 1;
      }
      return evaluatedTemplateArr.join("");
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getReferenceValue.js
var getReferenceValue;
var init_getReferenceValue = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getReferenceValue.js"() {
    getReferenceValue = ({ ref }, options) => {
      return options.referenceRecord[ref] ?? options.endpointParams[ref];
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateExpression.js
var evaluateExpression, callFunction, group;
var init_evaluateExpression = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateExpression.js"() {
    init_types();
    init_customEndpointFunctions();
    init_endpointFunctions();
    init_evaluateTemplate();
    init_getReferenceValue();
    evaluateExpression = (obj, keyName, options) => {
      if (typeof obj === "string") {
        return evaluateTemplate(obj, options);
      } else if (obj["fn"]) {
        return group.callFunction(obj, options);
      } else if (obj["ref"]) {
        return getReferenceValue(obj, options);
      }
      throw new EndpointError(`'${keyName}': ${String(obj)} is not a string, function or reference.`);
    };
    callFunction = ({ fn, argv }, options) => {
      const evaluatedArgs = Array(argv.length);
      for (let i2 = 0; i2 < evaluatedArgs.length; ++i2) {
        const arg = argv[i2];
        if (typeof arg === "boolean" || typeof arg === "number") {
          evaluatedArgs[i2] = arg;
        } else {
          evaluatedArgs[i2] = group.evaluateExpression(arg, "arg", options);
        }
      }
      const namespaceSeparatorIndex = fn.indexOf(".");
      if (namespaceSeparatorIndex !== -1) {
        const namespaceFunctions = customEndpointFunctions[fn.slice(0, namespaceSeparatorIndex)];
        const customFunction = namespaceFunctions?.[fn.slice(namespaceSeparatorIndex + 1)];
        if (typeof customFunction === "function") {
          return customFunction(...evaluatedArgs);
        }
      }
      const callable = endpointFunctions[fn];
      if (typeof callable === "function") {
        return callable(...evaluatedArgs);
      }
      throw new Error(`function ${fn} not loaded in endpointFunctions.`);
    };
    group = {
      evaluateExpression,
      callFunction
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/callFunction.js
var init_callFunction = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/callFunction.js"() {
    init_evaluateExpression();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateCondition.js
var evaluateCondition;
var init_evaluateCondition = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateCondition.js"() {
    init_debug();
    init_types();
    init_callFunction();
    evaluateCondition = (condition, options) => {
      const { assign } = condition;
      if (assign && assign in options.referenceRecord) {
        throw new EndpointError(`'${assign}' is already defined in Reference Record.`);
      }
      const value = callFunction(condition, options);
      options.logger?.debug?.(`${debugId} evaluateCondition: ${toDebugString(condition)} = ${toDebugString(value)}`);
      const result = value === "" ? true : !!value;
      if (assign != null) {
        return { result, toAssign: { name: assign, value } };
      }
      return { result };
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getEndpointHeaders.js
var getEndpointHeaders;
var init_getEndpointHeaders = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getEndpointHeaders.js"() {
    init_types();
    init_evaluateExpression();
    getEndpointHeaders = (headers, options) => Object.entries(headers ?? {}).reduce((acc, [headerKey, headerVal]) => {
      acc[headerKey] = headerVal.map((headerValEntry) => {
        const processedExpr = evaluateExpression(headerValEntry, "Header value entry", options);
        if (typeof processedExpr !== "string") {
          throw new EndpointError(`Header '${headerKey}' value '${processedExpr}' is not a string`);
        }
        return processedExpr;
      });
      return acc;
    }, {});
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getEndpointProperties.js
var getEndpointProperties, getEndpointProperty, group2;
var init_getEndpointProperties = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getEndpointProperties.js"() {
    init_types();
    init_evaluateTemplate();
    getEndpointProperties = (properties, options) => Object.entries(properties).reduce((acc, [propertyKey, propertyVal]) => {
      acc[propertyKey] = group2.getEndpointProperty(propertyVal, options);
      return acc;
    }, {});
    getEndpointProperty = (property, options) => {
      if (Array.isArray(property)) {
        return property.map((propertyEntry) => getEndpointProperty(propertyEntry, options));
      }
      switch (typeof property) {
        case "string":
          return evaluateTemplate(property, options);
        case "object":
          if (property === null) {
            throw new EndpointError(`Unexpected endpoint property: ${property}`);
          }
          return group2.getEndpointProperties(property, options);
        case "boolean":
          return property;
        default:
          throw new EndpointError(`Unexpected endpoint property type: ${typeof property}`);
      }
    };
    group2 = {
      getEndpointProperty,
      getEndpointProperties
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getEndpointUrl.js
var getEndpointUrl;
var init_getEndpointUrl = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/getEndpointUrl.js"() {
    init_types();
    init_evaluateExpression();
    getEndpointUrl = (endpointUrl, options) => {
      const expression = evaluateExpression(endpointUrl, "Endpoint URL", options);
      if (typeof expression === "string") {
        try {
          return new URL(expression);
        } catch (error) {
          console.error(`Failed to construct URL with ${expression}`, error);
          throw error;
        }
      }
      throw new EndpointError(`Endpoint URL must be a string, got ${typeof expression}`);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateConditions.js
var evaluateConditions;
var init_evaluateConditions = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateConditions.js"() {
    init_debug();
    init_evaluateCondition();
    evaluateConditions = (conditions = [], options) => {
      const conditionsReferenceRecord = {};
      const conditionOptions = {
        ...options,
        referenceRecord: { ...options.referenceRecord }
      };
      let didAssign = false;
      for (const condition of conditions) {
        const { result, toAssign } = evaluateCondition(condition, conditionOptions);
        if (!result) {
          return { result };
        }
        if (toAssign) {
          didAssign = true;
          conditionsReferenceRecord[toAssign.name] = toAssign.value;
          conditionOptions.referenceRecord[toAssign.name] = toAssign.value;
          options.logger?.debug?.(`${debugId} assign: ${toAssign.name} := ${toDebugString(toAssign.value)}`);
        }
      }
      if (didAssign) {
        return { result: true, referenceRecord: conditionsReferenceRecord };
      }
      return { result: true };
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateEndpointRule.js
var evaluateEndpointRule;
var init_evaluateEndpointRule = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateEndpointRule.js"() {
    init_debug();
    init_evaluateConditions();
    init_getEndpointHeaders();
    init_getEndpointProperties();
    init_getEndpointUrl();
    evaluateEndpointRule = (endpointRule, options) => {
      const { conditions, endpoint } = endpointRule;
      const { result, referenceRecord } = evaluateConditions(conditions, options);
      if (!result) {
        return;
      }
      const endpointRuleOptions = referenceRecord ? {
        ...options,
        referenceRecord: { ...options.referenceRecord, ...referenceRecord }
      } : options;
      const { url, properties, headers } = endpoint;
      options.logger?.debug?.(`${debugId} Resolving endpoint from template: ${toDebugString(endpoint)}`);
      const endpointToReturn = { url: getEndpointUrl(url, endpointRuleOptions) };
      if (headers != null) {
        endpointToReturn.headers = getEndpointHeaders(headers, endpointRuleOptions);
      }
      if (properties != null) {
        endpointToReturn.properties = getEndpointProperties(properties, endpointRuleOptions);
      }
      return endpointToReturn;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateErrorRule.js
var evaluateErrorRule;
var init_evaluateErrorRule = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateErrorRule.js"() {
    init_types();
    init_evaluateConditions();
    init_evaluateExpression();
    evaluateErrorRule = (errorRule, options) => {
      const { conditions, error } = errorRule;
      const { result, referenceRecord } = evaluateConditions(conditions, options);
      if (!result) {
        return;
      }
      const errorRuleOptions = referenceRecord ? {
        ...options,
        referenceRecord: { ...options.referenceRecord, ...referenceRecord }
      } : options;
      throw new EndpointError(evaluateExpression(error, "Error", errorRuleOptions));
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateRules.js
var evaluateRules, evaluateTreeRule, group3;
var init_evaluateRules = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/evaluateRules.js"() {
    init_types();
    init_evaluateConditions();
    init_evaluateEndpointRule();
    init_evaluateErrorRule();
    evaluateRules = (rules, options) => {
      for (const rule of rules) {
        if (rule.type === "endpoint") {
          const endpointOrUndefined = evaluateEndpointRule(rule, options);
          if (endpointOrUndefined) {
            return endpointOrUndefined;
          }
        } else if (rule.type === "error") {
          evaluateErrorRule(rule, options);
        } else if (rule.type === "tree") {
          const endpointOrUndefined = group3.evaluateTreeRule(rule, options);
          if (endpointOrUndefined) {
            return endpointOrUndefined;
          }
        } else {
          throw new EndpointError(`Unknown endpoint rule: ${rule}`);
        }
      }
      throw new EndpointError(`Rules evaluation failed`);
    };
    evaluateTreeRule = (treeRule, options) => {
      const { conditions, rules } = treeRule;
      const { result, referenceRecord } = evaluateConditions(conditions, options);
      if (!result) {
        return;
      }
      const treeRuleOptions = referenceRecord ? { ...options, referenceRecord: { ...options.referenceRecord, ...referenceRecord } } : options;
      return group3.evaluateRules(rules, treeRuleOptions);
    };
    group3 = {
      evaluateRules,
      evaluateTreeRule
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/index.js
var init_utils = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/utils/index.js"() {
    init_evaluateRules();
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/resolveEndpoint.js
var resolveEndpoint;
var init_resolveEndpoint = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/util-endpoints/resolveEndpoint.js"() {
    init_debug();
    init_types();
    init_utils();
    resolveEndpoint = (ruleSetObject, options) => {
      const { endpointParams, logger: logger2 } = options;
      const { parameters, rules } = ruleSetObject;
      options.logger?.debug?.(`${debugId} Initial EndpointParams: ${toDebugString(endpointParams)}`);
      for (const paramKey in parameters) {
        const parameter = parameters[paramKey];
        const endpointParam = endpointParams[paramKey];
        if (endpointParam == null && parameter.default != null) {
          endpointParams[paramKey] = parameter.default;
          continue;
        }
        if (parameter.required && endpointParam == null) {
          throw new EndpointError(`Missing required parameter: '${paramKey}'`);
        }
      }
      const endpoint = evaluateRules(rules, { endpointParams, logger: logger2, referenceRecord: {} });
      options.logger?.debug?.(`${debugId} Resolved endpoint: ${toDebugString(endpoint)}`);
      return endpoint;
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/endpoints/index.browser.js
var getEndpointFromInstructions, resolveEndpointConfig, endpointMiddleware, getEndpointPlugin;
var init_index_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/endpoints/index.browser.js"() {
    init_getEndpointFromConfig_browser();
    init_getEndpointFromInstructions();
    init_endpointMiddleware();
    init_getEndpointPlugin();
    init_resolveEndpointConfig();
    init_EndpointCache();
    init_isIpAddress();
    init_transport();
    init_customEndpointFunctions();
    init_resolveEndpoint();
    getEndpointFromInstructions = bindGetEndpointFromInstructions(getEndpointFromConfig);
    resolveEndpointConfig = bindResolveEndpointConfig(getEndpointFromConfig);
    endpointMiddleware = bindEndpointMiddleware(getEndpointFromConfig);
    getEndpointPlugin = bindGetEndpointPlugin(getEndpointFromConfig);
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-stream/stream-type-check.js
var isReadableStream, isBlob;
var init_stream_type_check = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-stream/stream-type-check.js"() {
    isReadableStream = (stream) => typeof ReadableStream === "function" && (stream?.constructor?.name === ReadableStream.name || stream instanceof ReadableStream);
    isBlob = (blob) => {
      return typeof Blob === "function" && (blob?.constructor?.name === Blob.name || blob instanceof Blob);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-stream/stream-collector.browser.js
async function collectBlob(blob) {
  return blob.arrayBuffer().then((ab) => new Uint8Array(ab));
}
async function collectReadableStream(stream) {
  const chunks = [];
  const reader = stream.getReader();
  let length = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (value) {
      chunks.push(value);
      length += value.length;
    }
    if (done) {
      break;
    }
  }
  return concatBytes(chunks, length);
}
var streamCollector;
var init_stream_collector_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-stream/stream-collector.browser.js"() {
    init_concatBytes();
    init_stream_type_check();
    streamCollector = async (stream) => {
      if (isBlob(stream)) {
        return collectBlob(stream);
      }
      return collectReadableStream(stream);
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/util-stream/sdk-stream-mixin.browser.js
var ERR_MSG_STREAM_HAS_BEEN_TRANSFORMED, sdkStreamMixin, isBlobInstance;
var init_sdk_stream_mixin_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/util-stream/sdk-stream-mixin.browser.js"() {
    init_toBase64_browser();
    init_hex_encoding();
    init_toUtf8_browser();
    init_stream_collector_browser();
    init_stream_type_check();
    ERR_MSG_STREAM_HAS_BEEN_TRANSFORMED = "The stream has already been transformed.";
    sdkStreamMixin = (stream) => {
      if (!isBlobInstance(stream) && !isReadableStream(stream)) {
        const name = stream?.__proto__?.constructor?.name || stream;
        throw new Error(`Unexpected stream implementation, expect Blob or ReadableStream, got ${name}`);
      }
      let transformed = false;
      const transformToByteArray = async () => {
        if (transformed) {
          throw new Error(ERR_MSG_STREAM_HAS_BEEN_TRANSFORMED);
        }
        transformed = true;
        return await streamCollector(stream);
      };
      const blobToWebStream = (blob) => {
        if (typeof blob.stream !== "function") {
          throw new Error("Cannot transform payload Blob to web stream. Please make sure the Blob.stream() is polyfilled.\nIf you are using React Native, this API is not yet supported, see: https://react-native.canny.io/feature-requests/p/fetch-streaming-body");
        }
        return blob.stream();
      };
      return Object.assign(stream, {
        transformToByteArray,
        transformToString: async (encoding) => {
          const buf = await transformToByteArray();
          if (encoding === "base64") {
            return toBase64(buf);
          } else if (encoding === "hex") {
            return toHex(buf);
          } else if (encoding === void 0 || encoding === "utf8" || encoding === "utf-8") {
            return toUtf8(buf);
          } else if (typeof TextDecoder === "function") {
            return new TextDecoder(encoding).decode(buf);
          } else {
            throw new Error("TextDecoder is not available, please make sure polyfill is provided.");
          }
        },
        transformToWebStream: () => {
          if (transformed) {
            throw new Error(ERR_MSG_STREAM_HAS_BEEN_TRANSFORMED);
          }
          transformed = true;
          if (isBlobInstance(stream)) {
            return blobToWebStream(stream);
          } else if (isReadableStream(stream)) {
            return stream;
          } else {
            throw new Error(`Cannot transform payload to web stream, got ${stream}`);
          }
        }
      });
    };
    isBlobInstance = (stream) => typeof Blob === "function" && stream instanceof Blob;
  }
});

// node_modules/@smithy/core/dist-es/submodules/serde/index.browser.js
var Uint8ArrayBlobAdapter, _getRandomValues, v4, generateIdempotencyToken;
var init_index_browser2 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/serde/index.browser.js"() {
    init_fromBase64_browser();
    init_toBase64_browser();
    init_Uint8ArrayBlobAdapter();
    init_fromUtf8_browser();
    init_toUtf8_browser();
    init_v4();
    init_date_utils();
    init_lazy_json();
    init_quote_header();
    init_schema_date_utils();
    init_split_every();
    init_split_header();
    init_NumericValue();
    init_hex_encoding();
    init_calculateBodyLength_browser();
    init_toUint8Array_browser();
    init_is_array_buffer();
    init_sdk_stream_mixin_browser();
    init_stream_collector_browser();
    Uint8ArrayBlobAdapter = class extends bindUint8ArrayBlobAdapter(toUtf8, fromUtf8, toBase64, fromBase64) {
    };
    _getRandomValues = (array) => crypto.getRandomValues(array);
    v4 = bindV4(_getRandomValues);
    generateIdempotencyToken = v4;
  }
});

// node_modules/@smithy/core/dist-es/submodules/checksum/crc32/Crc32Js.js
var CRC32_TABLE, ONES, Crc32Js;
var init_Crc32Js = __esm({
  "node_modules/@smithy/core/dist-es/submodules/checksum/crc32/Crc32Js.js"() {
    CRC32_TABLE = new Uint32Array(256);
    for (let i2 = 0; i2 < 256; ++i2) {
      let c2 = i2;
      for (let j2 = 0; j2 < 8; ++j2) {
        c2 = c2 & 1 ? 3988292384 ^ c2 >>> 1 : c2 >>> 1;
      }
      CRC32_TABLE[i2] = c2 >>> 0;
    }
    ONES = 4294967295;
    Crc32Js = class {
      digestLength = 4;
      checksum = ONES;
      update(data) {
        for (let i2 = 0; i2 < data.length; ++i2) {
          this.checksum = this.checksum >>> 8 ^ CRC32_TABLE[(this.checksum ^ data[i2]) & 255];
        }
      }
      digestSync() {
        return (this.checksum ^ ONES) >>> 0;
      }
      async digest() {
        const value = this.digestSync();
        const out = new Uint8Array(4);
        new DataView(out.buffer).setUint32(0, value, false);
        return out;
      }
      reset() {
        this.checksum = ONES;
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/checksum/index.browser.js
var init_index_browser3 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/checksum/index.browser.js"() {
    init_Crc32Js();
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/Int64.js
function negate(bytes) {
  for (let i2 = 0; i2 < 8; i2++) {
    bytes[i2] ^= 255;
  }
  for (let i2 = 7; i2 > -1; i2--) {
    bytes[i2]++;
    if (bytes[i2] !== 0)
      break;
  }
}
var Int64;
var init_Int64 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/Int64.js"() {
    init_index_browser2();
    Int64 = class _Int64 {
      bytes;
      constructor(bytes) {
        this.bytes = bytes;
        if (bytes.byteLength !== 8) {
          throw new Error("Int64 buffers must be exactly 8 bytes");
        }
      }
      static fromNumber(number) {
        if (number > 9223372036854776e3 || number < -9223372036854776e3) {
          throw new Error(`${number} is too large (or, if negative, too small) to represent as an Int64`);
        }
        const bytes = new Uint8Array(8);
        for (let i2 = 7, remaining = Math.abs(Math.round(number)); i2 > -1 && remaining > 0; i2--, remaining /= 256) {
          bytes[i2] = remaining;
        }
        if (number < 0) {
          negate(bytes);
        }
        return new _Int64(bytes);
      }
      valueOf() {
        const bytes = this.bytes.slice(0);
        const negative = bytes[0] & 128;
        if (negative) {
          negate(bytes);
        }
        return parseInt(toHex(bytes), 16) * (negative ? -1 : 1);
      }
      toString() {
        return String(this.valueOf());
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/HeaderMarshaller.js
var HeaderMarshaller, HEADER_VALUE_TYPE, BOOLEAN_TAG, BYTE_TAG, SHORT_TAG, INT_TAG, LONG_TAG, BINARY_TAG, STRING_TAG, TIMESTAMP_TAG, UUID_TAG, UUID_PATTERN;
var init_HeaderMarshaller = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/HeaderMarshaller.js"() {
    init_index_browser2();
    init_Int64();
    HeaderMarshaller = class {
      toUtf8;
      fromUtf8;
      constructor(toUtf82, fromUtf84) {
        this.toUtf8 = toUtf82;
        this.fromUtf8 = fromUtf84;
      }
      format(headers) {
        const chunks = [];
        for (const headerName of Object.keys(headers)) {
          const bytes = this.fromUtf8(headerName);
          chunks.push(Uint8Array.from([bytes.byteLength]), bytes, this.formatHeaderValue(headers[headerName]));
        }
        const out = new Uint8Array(chunks.reduce((carry, bytes) => carry + bytes.byteLength, 0));
        let position = 0;
        for (const chunk of chunks) {
          out.set(chunk, position);
          position += chunk.byteLength;
        }
        return out;
      }
      formatHeaderValue(header) {
        switch (header.type) {
          case "boolean":
            return Uint8Array.from([header.value ? 0 : 1]);
          case "byte":
            return Uint8Array.from([2, header.value]);
          case "short":
            const shortView = new DataView(new ArrayBuffer(3));
            shortView.setUint8(0, 3);
            shortView.setInt16(1, header.value, false);
            return new Uint8Array(shortView.buffer);
          case "integer":
            const intView = new DataView(new ArrayBuffer(5));
            intView.setUint8(0, 4);
            intView.setInt32(1, header.value, false);
            return new Uint8Array(intView.buffer);
          case "long":
            const longBytes = new Uint8Array(9);
            longBytes[0] = 5;
            longBytes.set(header.value.bytes, 1);
            return longBytes;
          case "binary":
            const binView = new DataView(new ArrayBuffer(3 + header.value.byteLength));
            binView.setUint8(0, 6);
            binView.setUint16(1, header.value.byteLength, false);
            const binBytes = new Uint8Array(binView.buffer);
            binBytes.set(header.value, 3);
            return binBytes;
          case "string":
            const utf8Bytes = this.fromUtf8(header.value);
            const strView = new DataView(new ArrayBuffer(3 + utf8Bytes.byteLength));
            strView.setUint8(0, 7);
            strView.setUint16(1, utf8Bytes.byteLength, false);
            const strBytes = new Uint8Array(strView.buffer);
            strBytes.set(utf8Bytes, 3);
            return strBytes;
          case "timestamp":
            const tsBytes = new Uint8Array(9);
            tsBytes[0] = 8;
            tsBytes.set(Int64.fromNumber(header.value.valueOf()).bytes, 1);
            return tsBytes;
          case "uuid":
            if (!UUID_PATTERN.test(header.value)) {
              throw new Error(`Invalid UUID received: ${header.value}`);
            }
            const uuidBytes = new Uint8Array(17);
            uuidBytes[0] = 9;
            uuidBytes.set(fromHex(header.value.replace(/\-/g, "")), 1);
            return uuidBytes;
        }
      }
      parse(headers) {
        const out = {};
        let position = 0;
        while (position < headers.byteLength) {
          const nameLength = headers.getUint8(position++);
          const name = this.toUtf8(new Uint8Array(headers.buffer, headers.byteOffset + position, nameLength));
          position += nameLength;
          switch (headers.getUint8(position++)) {
            case 0:
              out[name] = {
                type: BOOLEAN_TAG,
                value: true
              };
              break;
            case 1:
              out[name] = {
                type: BOOLEAN_TAG,
                value: false
              };
              break;
            case 2:
              out[name] = {
                type: BYTE_TAG,
                value: headers.getInt8(position++)
              };
              break;
            case 3:
              out[name] = {
                type: SHORT_TAG,
                value: headers.getInt16(position, false)
              };
              position += 2;
              break;
            case 4:
              out[name] = {
                type: INT_TAG,
                value: headers.getInt32(position, false)
              };
              position += 4;
              break;
            case 5:
              out[name] = {
                type: LONG_TAG,
                value: new Int64(new Uint8Array(headers.buffer, headers.byteOffset + position, 8))
              };
              position += 8;
              break;
            case 6:
              const binaryLength = headers.getUint16(position, false);
              position += 2;
              out[name] = {
                type: BINARY_TAG,
                value: new Uint8Array(headers.buffer, headers.byteOffset + position, binaryLength)
              };
              position += binaryLength;
              break;
            case 7:
              const stringLength = headers.getUint16(position, false);
              position += 2;
              out[name] = {
                type: STRING_TAG,
                value: this.toUtf8(new Uint8Array(headers.buffer, headers.byteOffset + position, stringLength))
              };
              position += stringLength;
              break;
            case 8:
              out[name] = {
                type: TIMESTAMP_TAG,
                value: new Date(new Int64(new Uint8Array(headers.buffer, headers.byteOffset + position, 8)).valueOf())
              };
              position += 8;
              break;
            case 9:
              const uuidBytes = new Uint8Array(headers.buffer, headers.byteOffset + position, 16);
              position += 16;
              out[name] = {
                type: UUID_TAG,
                value: `${toHex(uuidBytes.subarray(0, 4))}-${toHex(uuidBytes.subarray(4, 6))}-${toHex(uuidBytes.subarray(6, 8))}-${toHex(uuidBytes.subarray(8, 10))}-${toHex(uuidBytes.subarray(10))}`
              };
              break;
            default:
              throw new Error(`Unrecognized header type tag`);
          }
        }
        return out;
      }
    };
    (function(HEADER_VALUE_TYPE3) {
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["boolTrue"] = 0] = "boolTrue";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["boolFalse"] = 1] = "boolFalse";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["byte"] = 2] = "byte";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["short"] = 3] = "short";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["integer"] = 4] = "integer";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["long"] = 5] = "long";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["byteArray"] = 6] = "byteArray";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["string"] = 7] = "string";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["timestamp"] = 8] = "timestamp";
      HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["uuid"] = 9] = "uuid";
    })(HEADER_VALUE_TYPE || (HEADER_VALUE_TYPE = {}));
    BOOLEAN_TAG = "boolean";
    BYTE_TAG = "byte";
    SHORT_TAG = "short";
    INT_TAG = "integer";
    LONG_TAG = "long";
    BINARY_TAG = "binary";
    STRING_TAG = "string";
    TIMESTAMP_TAG = "timestamp";
    UUID_TAG = "uuid";
    UUID_PATTERN = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/splitMessage.js
function splitMessage({ byteLength, byteOffset, buffer }) {
  if (byteLength < MINIMUM_MESSAGE_LENGTH) {
    throw new Error("Provided message too short to accommodate event stream message overhead");
  }
  const view = new DataView(buffer, byteOffset, byteLength);
  const messageLength = view.getUint32(0, false);
  if (byteLength !== messageLength) {
    throw new Error("Reported message length does not match received message length");
  }
  const headerLength = view.getUint32(PRELUDE_MEMBER_LENGTH, false);
  const expectedPreludeChecksum = view.getUint32(PRELUDE_LENGTH, false);
  const expectedMessageChecksum = view.getUint32(byteLength - CHECKSUM_LENGTH, false);
  const checksummer = new Crc32Js();
  checksummer.update(new Uint8Array(buffer, byteOffset, PRELUDE_LENGTH));
  if (expectedPreludeChecksum !== checksummer.digestSync()) {
    throw new Error(`The prelude checksum specified in the message (${expectedPreludeChecksum}) does not match the calculated CRC32 checksum (${checksummer.digestSync()})`);
  }
  checksummer.update(new Uint8Array(buffer, byteOffset + PRELUDE_LENGTH, byteLength - (PRELUDE_LENGTH + CHECKSUM_LENGTH)));
  if (expectedMessageChecksum !== checksummer.digestSync()) {
    throw new Error(`The message checksum (${checksummer.digestSync()}) did not match the expected value of ${expectedMessageChecksum}`);
  }
  return {
    headers: new DataView(buffer, byteOffset + PRELUDE_LENGTH + CHECKSUM_LENGTH, headerLength),
    body: new Uint8Array(buffer, byteOffset + PRELUDE_LENGTH + CHECKSUM_LENGTH + headerLength, messageLength - headerLength - (PRELUDE_LENGTH + CHECKSUM_LENGTH + CHECKSUM_LENGTH))
  };
}
var PRELUDE_MEMBER_LENGTH, PRELUDE_LENGTH, CHECKSUM_LENGTH, MINIMUM_MESSAGE_LENGTH;
var init_splitMessage = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/splitMessage.js"() {
    init_index_browser3();
    PRELUDE_MEMBER_LENGTH = 4;
    PRELUDE_LENGTH = PRELUDE_MEMBER_LENGTH * 2;
    CHECKSUM_LENGTH = 4;
    MINIMUM_MESSAGE_LENGTH = PRELUDE_LENGTH + CHECKSUM_LENGTH * 2;
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/EventStreamCodec.js
var EventStreamCodec;
var init_EventStreamCodec = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/EventStreamCodec.js"() {
    init_index_browser3();
    init_HeaderMarshaller();
    init_splitMessage();
    EventStreamCodec = class {
      headerMarshaller;
      messageBuffer;
      isEndOfStream;
      constructor(toUtf82, fromUtf84) {
        this.headerMarshaller = new HeaderMarshaller(toUtf82, fromUtf84);
        this.messageBuffer = [];
        this.isEndOfStream = false;
      }
      feed(message) {
        this.messageBuffer.push(this.decode(message));
      }
      endOfStream() {
        this.isEndOfStream = true;
      }
      getMessage() {
        const message = this.messageBuffer.pop();
        const isEndOfStream = this.isEndOfStream;
        return {
          getMessage() {
            return message;
          },
          isEndOfStream() {
            return isEndOfStream;
          }
        };
      }
      getAvailableMessages() {
        const messages = this.messageBuffer;
        this.messageBuffer = [];
        const isEndOfStream = this.isEndOfStream;
        return {
          getMessages() {
            return messages;
          },
          isEndOfStream() {
            return isEndOfStream;
          }
        };
      }
      encode({ headers: rawHeaders, body }) {
        const headers = this.headerMarshaller.format(rawHeaders);
        const length = headers.byteLength + body.byteLength + 16;
        const out = new Uint8Array(length);
        const view = new DataView(out.buffer, out.byteOffset, out.byteLength);
        const checksum = new Crc32Js();
        view.setUint32(0, length, false);
        view.setUint32(4, headers.byteLength, false);
        checksum.update(out.subarray(0, 8));
        view.setUint32(8, checksum.digestSync(), false);
        out.set(headers, 12);
        out.set(body, headers.byteLength + 12);
        checksum.update(out.subarray(8, length - 4));
        view.setUint32(length - 4, checksum.digestSync(), false);
        return out;
      }
      decode(message) {
        const { headers, body } = splitMessage(message);
        return { headers: this.headerMarshaller.parse(headers), body };
      }
      formatHeaders(rawHeaders) {
        return this.headerMarshaller.format(rawHeaders);
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/MessageDecoderStream.js
var MessageDecoderStream;
var init_MessageDecoderStream = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/MessageDecoderStream.js"() {
    MessageDecoderStream = class {
      options;
      constructor(options) {
        this.options = options;
      }
      [Symbol.asyncIterator]() {
        return this.asyncIterator();
      }
      async *asyncIterator() {
        for await (const bytes of this.options.inputStream) {
          const decoded = this.options.decoder.decode(bytes);
          yield decoded;
        }
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/MessageEncoderStream.js
var MessageEncoderStream;
var init_MessageEncoderStream = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/MessageEncoderStream.js"() {
    MessageEncoderStream = class {
      options;
      constructor(options) {
        this.options = options;
      }
      [Symbol.asyncIterator]() {
        return this.asyncIterator();
      }
      async *asyncIterator() {
        for await (const msg of this.options.messageStream) {
          const encoded = this.options.encoder.encode(msg);
          yield encoded;
        }
        if (this.options.includeEndFrame) {
          yield new Uint8Array(0);
        }
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/SmithyMessageDecoderStream.js
var SmithyMessageDecoderStream;
var init_SmithyMessageDecoderStream = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/SmithyMessageDecoderStream.js"() {
    SmithyMessageDecoderStream = class {
      options;
      constructor(options) {
        this.options = options;
      }
      [Symbol.asyncIterator]() {
        return this.asyncIterator();
      }
      async *asyncIterator() {
        for await (const message of this.options.messageStream) {
          const deserialized = await this.options.deserializer(message);
          if (deserialized === void 0)
            continue;
          yield deserialized;
        }
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/SmithyMessageEncoderStream.js
var SmithyMessageEncoderStream;
var init_SmithyMessageEncoderStream = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-codec/SmithyMessageEncoderStream.js"() {
    SmithyMessageEncoderStream = class {
      options;
      constructor(options) {
        this.options = options;
      }
      [Symbol.asyncIterator]() {
        return this.asyncIterator();
      }
      async *asyncIterator() {
        for await (const chunk of this.options.inputStream) {
          const payloadBuf = this.options.serializer(chunk);
          yield payloadBuf;
        }
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-universal/getChunkedStream.js
function getChunkedStream(source) {
  let currentMessageTotalLength = 0;
  let currentMessagePendingLength = 0;
  let currentMessage = null;
  let messageLengthBuffer = null;
  const allocateMessage = (size) => {
    if (typeof size !== "number") {
      throw new Error("Attempted to allocate an event message where size was not a number: " + size);
    }
    currentMessageTotalLength = size;
    currentMessagePendingLength = 4;
    currentMessage = new Uint8Array(size);
    const currentMessageView = new DataView(currentMessage.buffer);
    currentMessageView.setUint32(0, size, false);
  };
  const iterator = async function* () {
    const sourceIterator = source[Symbol.asyncIterator]();
    while (true) {
      const { value, done } = await sourceIterator.next();
      if (done) {
        if (!currentMessageTotalLength) {
          return;
        } else if (currentMessageTotalLength === currentMessagePendingLength) {
          yield currentMessage;
        } else {
          throw new Error("Truncated event message received.");
        }
        return;
      }
      const chunkLength = value.length;
      let currentOffset = 0;
      while (currentOffset < chunkLength) {
        if (!currentMessage) {
          const bytesRemaining = chunkLength - currentOffset;
          if (!messageLengthBuffer) {
            messageLengthBuffer = new Uint8Array(4);
          }
          const numBytesForTotal = Math.min(4 - currentMessagePendingLength, bytesRemaining);
          messageLengthBuffer.set(value.slice(currentOffset, currentOffset + numBytesForTotal), currentMessagePendingLength);
          currentMessagePendingLength += numBytesForTotal;
          currentOffset += numBytesForTotal;
          if (currentMessagePendingLength < 4) {
            break;
          }
          allocateMessage(new DataView(messageLengthBuffer.buffer).getUint32(0, false));
          messageLengthBuffer = null;
        }
        const numBytesToWrite = Math.min(currentMessageTotalLength - currentMessagePendingLength, chunkLength - currentOffset);
        currentMessage.set(value.slice(currentOffset, currentOffset + numBytesToWrite), currentMessagePendingLength);
        currentMessagePendingLength += numBytesToWrite;
        currentOffset += numBytesToWrite;
        if (currentMessageTotalLength && currentMessageTotalLength === currentMessagePendingLength) {
          yield currentMessage;
          currentMessage = null;
          currentMessageTotalLength = 0;
          currentMessagePendingLength = 0;
        }
      }
    }
  };
  return {
    [Symbol.asyncIterator]: iterator
  };
}
var init_getChunkedStream = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-universal/getChunkedStream.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-universal/getUnmarshalledStream.js
function getUnmarshalledStream(source, options) {
  const messageUnmarshaller = getMessageUnmarshaller(options.deserializer, options.toUtf8);
  return {
    [Symbol.asyncIterator]: async function* () {
      for await (const chunk of source) {
        const message = options.eventStreamCodec.decode(chunk);
        const type = await messageUnmarshaller(message);
        if (type === void 0)
          continue;
        yield type;
      }
    }
  };
}
function getMessageUnmarshaller(deserializer, toUtf82) {
  return async function(message) {
    const { value: messageType } = message.headers[":message-type"];
    if (messageType === "error") {
      const unmodeledError = new Error(message.headers[":error-message"].value || "UnknownError");
      unmodeledError.name = message.headers[":error-code"].value;
      throw unmodeledError;
    } else if (messageType === "exception") {
      const code = message.headers[":exception-type"].value;
      const exception = { [code]: message };
      const deserializedException = await deserializer(exception);
      if (deserializedException.$unknown) {
        const error = new Error(toUtf82(message.body));
        error.name = code;
        throw error;
      }
      throw deserializedException[code];
    } else if (messageType === "event") {
      const event = {
        [message.headers[":event-type"].value]: message
      };
      const deserialized = await deserializer(event);
      if (deserialized.$unknown)
        return;
      return deserialized;
    } else {
      throw Error(`Unrecognizable event type: ${message.headers[":event-type"].value}`);
    }
  };
}
var init_getUnmarshalledStream = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-universal/getUnmarshalledStream.js"() {
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-universal/EventStreamMarshaller.js
var EventStreamMarshaller, eventStreamSerdeProvider;
var init_EventStreamMarshaller = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-universal/EventStreamMarshaller.js"() {
    init_EventStreamCodec();
    init_MessageDecoderStream();
    init_MessageEncoderStream();
    init_SmithyMessageDecoderStream();
    init_SmithyMessageEncoderStream();
    init_getChunkedStream();
    init_getUnmarshalledStream();
    EventStreamMarshaller = class {
      eventStreamCodec;
      utfEncoder;
      constructor({ utf8Encoder, utf8Decoder }) {
        this.eventStreamCodec = new EventStreamCodec(utf8Encoder, utf8Decoder);
        this.utfEncoder = utf8Encoder;
      }
      deserialize(body, deserializer) {
        const inputStream = getChunkedStream(body);
        return new SmithyMessageDecoderStream({
          messageStream: new MessageDecoderStream({ inputStream, decoder: this.eventStreamCodec }),
          deserializer: getMessageUnmarshaller(deserializer, this.utfEncoder)
        });
      }
      serialize(inputStream, serializer) {
        return new MessageEncoderStream({
          messageStream: new SmithyMessageEncoderStream({ inputStream, serializer }),
          encoder: this.eventStreamCodec,
          includeEndFrame: true
        });
      }
    };
    eventStreamSerdeProvider = (options) => new EventStreamMarshaller(options);
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde/utils.js
var readableStreamToIterable, iterableToReadableStream;
var init_utils2 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde/utils.js"() {
    readableStreamToIterable = (readableStream) => ({
      [Symbol.asyncIterator]: async function* () {
        const reader = readableStream.getReader();
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done)
              return;
            yield value;
          }
        } finally {
          reader.releaseLock();
        }
      }
    });
    iterableToReadableStream = (asyncIterable) => {
      const iterator = asyncIterable[Symbol.asyncIterator]();
      return new ReadableStream({
        async pull(controller) {
          const { done, value } = await iterator.next();
          if (done) {
            return controller.close();
          }
          controller.enqueue(value);
        }
      });
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde/EventStreamMarshaller.browser.js
var EventStreamMarshaller2, isReadableStream2, eventStreamSerdeProvider2;
var init_EventStreamMarshaller_browser = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde/EventStreamMarshaller.browser.js"() {
    init_EventStreamMarshaller();
    init_utils2();
    EventStreamMarshaller2 = class {
      universalMarshaller;
      constructor({ utf8Encoder, utf8Decoder }) {
        this.universalMarshaller = new EventStreamMarshaller({
          utf8Decoder,
          utf8Encoder
        });
      }
      deserialize(body, deserializer) {
        const bodyIterable = isReadableStream2(body) ? readableStreamToIterable(body) : body;
        return this.universalMarshaller.deserialize(bodyIterable, deserializer);
      }
      serialize(input, serializer) {
        const serializedIterable = this.universalMarshaller.serialize(input, serializer);
        return typeof ReadableStream === "function" ? iterableToReadableStream(serializedIterable) : serializedIterable;
      }
    };
    isReadableStream2 = (body) => typeof ReadableStream === "function" && body instanceof ReadableStream;
    eventStreamSerdeProvider2 = (options) => new EventStreamMarshaller2(options);
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-config-resolver/EventStreamSerdeConfig.js
var resolveEventStreamSerdeConfig;
var init_EventStreamSerdeConfig = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/eventstream-serde-config-resolver/EventStreamSerdeConfig.js"() {
    resolveEventStreamSerdeConfig = (input) => Object.assign(input, {
      eventStreamMarshaller: input.eventStreamSerdeProvider(input)
    });
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/EventStreamSerde.js
var EventStreamSerde;
var init_EventStreamSerde = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/EventStreamSerde.js"() {
    init_index_browser2();
    EventStreamSerde = class {
      marshaller;
      serializer;
      deserializer;
      serdeContext;
      defaultContentType;
      constructor({ marshaller, serializer, deserializer, serdeContext, defaultContentType }) {
        this.marshaller = marshaller;
        this.serializer = serializer;
        this.deserializer = deserializer;
        this.serdeContext = serdeContext;
        this.defaultContentType = defaultContentType;
      }
      async serializeEventStream({ eventStream, requestSchema, initialRequest }) {
        const marshaller = this.marshaller;
        const eventStreamMember = requestSchema.getEventStreamMember();
        const unionSchema = requestSchema.getMemberSchema(eventStreamMember);
        const serializer = this.serializer;
        const defaultContentType = this.defaultContentType;
        const initialRequestMarker = /* @__PURE__ */ Symbol("initialRequestMarker");
        const eventStreamIterable = {
          async *[Symbol.asyncIterator]() {
            if (initialRequest) {
              const headers = {
                ":event-type": { type: "string", value: "initial-request" },
                ":message-type": { type: "string", value: "event" },
                ":content-type": { type: "string", value: defaultContentType }
              };
              serializer.write(requestSchema, initialRequest);
              const body = serializer.flush();
              yield {
                [initialRequestMarker]: true,
                headers,
                body
              };
            }
            for await (const page of eventStream) {
              yield page;
            }
          }
        };
        return marshaller.serialize(eventStreamIterable, (event) => {
          if (event[initialRequestMarker]) {
            return {
              headers: event.headers,
              body: event.body
            };
          }
          let unionMember = "";
          for (const key in event) {
            if (key !== "__type") {
              unionMember = key;
              break;
            }
          }
          const { additionalHeaders, body, eventType, explicitPayloadContentType } = this.writeEventBody(unionMember, unionSchema, event);
          const headers = {
            ":event-type": { type: "string", value: eventType },
            ":message-type": { type: "string", value: "event" },
            ":content-type": { type: "string", value: explicitPayloadContentType ?? defaultContentType },
            ...additionalHeaders
          };
          return {
            headers,
            body
          };
        });
      }
      async deserializeEventStream({ response, responseSchema, initialResponseContainer }) {
        const marshaller = this.marshaller;
        const eventStreamMember = responseSchema.getEventStreamMember();
        const unionSchema = responseSchema.getMemberSchema(eventStreamMember);
        const memberSchemas = unionSchema.getMemberSchemas();
        const initialResponseMarker = /* @__PURE__ */ Symbol("initialResponseMarker");
        const asyncIterable = marshaller.deserialize(response.body, async (event) => {
          let unionMember = "";
          for (const key in event) {
            if (key !== "__type") {
              unionMember = key;
              break;
            }
          }
          const body = event[unionMember].body;
          if (unionMember === "initial-response") {
            const dataObject = await this.deserializer.read(responseSchema, body);
            delete dataObject[eventStreamMember];
            return {
              [initialResponseMarker]: true,
              ...dataObject
            };
          } else if (unionMember in memberSchemas) {
            const eventStreamSchema = memberSchemas[unionMember];
            if (eventStreamSchema.isStructSchema()) {
              const out = {};
              let hasBindings = false;
              for (const [name, member2] of eventStreamSchema.structIterator()) {
                const { eventHeader, eventPayload } = member2.getMergedTraits();
                hasBindings = hasBindings || Boolean(eventHeader || eventPayload);
                if (eventPayload) {
                  if (member2.isBlobSchema()) {
                    out[name] = body;
                  } else if (member2.isStringSchema()) {
                    out[name] = (this.serdeContext?.utf8Encoder ?? toUtf8)(body);
                  } else if (member2.isStructSchema()) {
                    out[name] = await this.deserializer.read(member2, body);
                  }
                } else if (eventHeader) {
                  const value = event[unionMember].headers[name]?.value;
                  if (value != null) {
                    if (member2.isNumericSchema()) {
                      if (value && typeof value === "object" && "bytes" in value) {
                        out[name] = BigInt(value.toString());
                      } else {
                        out[name] = Number(value);
                      }
                    } else {
                      out[name] = value;
                    }
                  }
                }
              }
              if (hasBindings) {
                return {
                  [unionMember]: out
                };
              }
              if (body.byteLength === 0) {
                return {
                  [unionMember]: {}
                };
              }
            }
            return {
              [unionMember]: await this.deserializer.read(eventStreamSchema, body)
            };
          } else {
            return {
              $unknown: event
            };
          }
        });
        const asyncIterator = asyncIterable[Symbol.asyncIterator]();
        const firstEvent = await asyncIterator.next();
        if (firstEvent.done) {
          return asyncIterable;
        }
        if (firstEvent.value?.[initialResponseMarker]) {
          if (!responseSchema) {
            throw new Error("@smithy::core/protocols - initial-response event encountered in event stream but no response schema given.");
          }
          for (const key in firstEvent.value) {
            initialResponseContainer[key] = firstEvent.value[key];
          }
        }
        return {
          async *[Symbol.asyncIterator]() {
            if (!firstEvent?.value?.[initialResponseMarker]) {
              yield firstEvent.value;
            }
            while (true) {
              const { done, value } = await asyncIterator.next();
              if (done) {
                break;
              }
              yield value;
            }
          }
        };
      }
      writeEventBody(unionMember, unionSchema, event) {
        const serializer = this.serializer;
        let eventType = unionMember;
        let explicitPayloadMember = null;
        let explicitPayloadContentType;
        const isKnownSchema = (() => {
          const struct = unionSchema.getSchema();
          return struct[4].includes(unionMember);
        })();
        const additionalHeaders = {};
        if (!isKnownSchema) {
          const [type, value] = event[unionMember];
          eventType = type;
          serializer.write(15, value);
        } else {
          const eventSchema = unionSchema.getMemberSchema(unionMember);
          if (eventSchema.isStructSchema()) {
            for (const [memberName, memberSchema] of eventSchema.structIterator()) {
              const { eventHeader, eventPayload } = memberSchema.getMergedTraits();
              if (eventPayload) {
                explicitPayloadMember = memberName;
              } else if (eventHeader) {
                const value = event[unionMember][memberName];
                let type = "binary";
                if (memberSchema.isNumericSchema()) {
                  if ((-2) ** 31 <= value && value <= 2 ** 31 - 1) {
                    type = "integer";
                  } else {
                    type = "long";
                  }
                } else if (memberSchema.isTimestampSchema()) {
                  type = "timestamp";
                } else if (memberSchema.isStringSchema()) {
                  type = "string";
                } else if (memberSchema.isBooleanSchema()) {
                  type = "boolean";
                }
                if (value != null) {
                  additionalHeaders[memberName] = {
                    type,
                    value
                  };
                  delete event[unionMember][memberName];
                }
              }
            }
            if (explicitPayloadMember !== null) {
              const payloadSchema = eventSchema.getMemberSchema(explicitPayloadMember);
              if (payloadSchema.isBlobSchema()) {
                explicitPayloadContentType = "application/octet-stream";
              } else if (payloadSchema.isStringSchema()) {
                explicitPayloadContentType = "text/plain";
              }
              serializer.write(payloadSchema, event[unionMember][explicitPayloadMember]);
            } else {
              serializer.write(eventSchema, event[unionMember]);
            }
          } else if (eventSchema.isUnitSchema()) {
            serializer.write(eventSchema, {});
          } else {
            throw new Error("@smithy/core/event-streams - non-struct member not supported in event stream union.");
          }
        }
        const messageSerialization = serializer.flush() ?? new Uint8Array();
        const body = typeof messageSerialization === "string" ? (this.serdeContext?.utf8Decoder ?? fromUtf8)(messageSerialization) : messageSerialization;
        return {
          body,
          eventType,
          explicitPayloadContentType,
          additionalHeaders
        };
      }
    };
  }
});

// node_modules/@smithy/core/dist-es/submodules/event-streams/index.browser.js
var index_browser_exports = {};
__export(index_browser_exports, {
  EventStreamCodec: () => EventStreamCodec,
  EventStreamMarshaller: () => EventStreamMarshaller2,
  EventStreamSerde: () => EventStreamSerde,
  HeaderMarshaller: () => HeaderMarshaller,
  Int64: () => Int64,
  MessageDecoderStream: () => MessageDecoderStream,
  MessageEncoderStream: () => MessageEncoderStream,
  SmithyMessageDecoderStream: () => SmithyMessageDecoderStream,
  SmithyMessageEncoderStream: () => SmithyMessageEncoderStream,
  UniversalEventStreamMarshaller: () => EventStreamMarshaller,
  eventStreamSerdeProvider: () => eventStreamSerdeProvider2,
  getChunkedStream: () => getChunkedStream,
  getMessageUnmarshaller: () => getMessageUnmarshaller,
  getUnmarshalledStream: () => getUnmarshalledStream,
  iterableToReadableStream: () => iterableToReadableStream,
  readableStreamToIterable: () => readableStreamToIterable,
  resolveEventStreamSerdeConfig: () => resolveEventStreamSerdeConfig,
  universalEventStreamSerdeProvider: () => eventStreamSerdeProvider
});
var init_index_browser4 = __esm({
  "node_modules/@smithy/core/dist-es/submodules/event-streams/index.browser.js"() {
    init_EventStreamCodec();
    init_HeaderMarshaller();
    init_Int64();
    init_MessageDecoderStream();
    init_MessageEncoderStream();
    init_SmithyMessageDecoderStream();
    init_SmithyMessageEncoderStream();
    init_EventStreamMarshaller_browser();
    init_utils2();
    init_EventStreamMarshaller();
    init_getChunkedStream();
    init_getUnmarshalledStream();
    init_EventStreamSerdeConfig();
    init_EventStreamSerde();
  }
});

// node_modules/@smithy/core/dist-es/submodules/protocols/collect-stream-body.js
init_index_browser2();
var collectBody = async (streamBody = new Uint8Array(), context) => {
  if (streamBody instanceof Uint8Array) {
    return Uint8ArrayBlobAdapter.mutate(streamBody);
  }
  if (!streamBody) {
    return Uint8ArrayBlobAdapter.mutate(new Uint8Array());
  }
  const fromContext = context.streamCollector(streamBody);
  return Uint8ArrayBlobAdapter.mutate(await fromContext);
};

// node_modules/@smithy/core/dist-es/submodules/protocols/extended-encode-uri-component.js
function extendedEncodeURIComponent(str) {
  return encodeURIComponent(str).replace(/[!'()*]/g, function(c2) {
    return "%" + c2.charCodeAt(0).toString(16).toUpperCase();
  });
}

// node_modules/@smithy/core/dist-es/submodules/schema/deref.js
var deref = (schemaRef) => {
  if (typeof schemaRef === "function") {
    return schemaRef();
  }
  return schemaRef;
};

// node_modules/@smithy/core/dist-es/submodules/schema/middleware/schemaDeserializationMiddleware.js
init_transport();

// node_modules/@smithy/core/dist-es/submodules/schema/schemas/operation.js
var operation = (namespace, name, traits, input, output) => ({
  name,
  namespace,
  traits,
  input,
  output
});

// node_modules/@smithy/core/dist-es/submodules/schema/middleware/schemaDeserializationMiddleware.js
var schemaDeserializationMiddleware = (config) => (next, context) => async (args) => {
  const { response } = await next(args);
  const { operationSchema } = getSmithyContext(context);
  const [, ns, n2, t2, i2, o2] = operationSchema ?? [];
  try {
    const parsed = await config.protocol.deserializeResponse(operation(ns, n2, t2, i2, o2), {
      ...config,
      ...context
    }, response);
    return {
      response,
      output: parsed
    };
  } catch (error) {
    Object.defineProperty(error, "$response", {
      value: response,
      enumerable: false,
      writable: false,
      configurable: false
    });
    if (!("$metadata" in error)) {
      const hint = `Deserialization error: to see the raw response, inspect the hidden field {error}.$response on this object.`;
      try {
        error.message += "\n  " + hint;
      } catch (e2) {
        if (!context.logger || context.logger?.constructor?.name === "NoOpLogger") {
          console.warn(hint);
        } else {
          context.logger?.warn?.(hint);
        }
      }
      if (typeof error.$responseBodyText !== "undefined") {
        if (error.$response) {
          error.$response.body = error.$responseBodyText;
        }
      }
      try {
        if (HttpResponse.isInstance(response)) {
          const { headers = {}, statusCode } = response;
          const headerEntries = Object.entries(headers);
          error.$metadata = {
            httpStatusCode: statusCode,
            requestId: findHeader(/^x-[\w-]+-request-?id$/, headerEntries),
            extendedRequestId: findHeader(/^x-[\w-]+-id-2$/, headerEntries),
            cfId: findHeader(/^x-[\w-]+-cf-id$/, headerEntries)
          };
        }
      } catch (e2) {
      }
    }
    throw error;
  }
};
var findHeader = (pattern, headers) => {
  return (headers.find(([k2]) => {
    return k2.match(pattern);
  }) || [void 0, void 0])[1];
};

// node_modules/@smithy/core/dist-es/submodules/schema/middleware/schemaSerializationMiddleware.js
init_transport();
var schemaSerializationMiddleware = (config) => (next, context) => async (args) => {
  const { operationSchema } = getSmithyContext(context);
  const [, ns, n2, t2, i2, o2] = operationSchema ?? [];
  const endpoint = context.endpointV2 ? async () => toEndpointV1(context.endpointV2) : config.endpoint;
  const request = await config.protocol.serializeRequest(operation(ns, n2, t2, i2, o2), args.input, {
    ...config,
    ...context,
    endpoint
  });
  return next({
    ...args,
    request
  });
};

// node_modules/@smithy/core/dist-es/submodules/schema/middleware/getSchemaSerdePlugin.js
var deserializerMiddlewareOption = {
  name: "deserializerMiddleware",
  step: "deserialize",
  tags: ["DESERIALIZER"],
  override: true
};
var serializerMiddlewareOption2 = {
  name: "serializerMiddleware",
  step: "serialize",
  tags: ["SERIALIZER"],
  override: true
};
function getSchemaSerdePlugin(config) {
  return {
    applyToStack: (commandStack) => {
      commandStack.add(schemaSerializationMiddleware(config), serializerMiddlewareOption2);
      commandStack.add(schemaDeserializationMiddleware(config), deserializerMiddlewareOption);
      config.protocol.setSerdeContext(config);
    }
  };
}

// node_modules/@smithy/core/dist-es/submodules/schema/schemas/translateTraits.js
var traitsCache = [];
function translateTraits(indicator) {
  if (typeof indicator === "object") {
    return indicator;
  }
  indicator = indicator | 0;
  if (traitsCache[indicator]) {
    return traitsCache[indicator];
  }
  const traits = {};
  let i2 = 0;
  for (const trait of [
    "httpLabel",
    "idempotent",
    "idempotencyToken",
    "sensitive",
    "httpPayload",
    "httpResponseCode",
    "httpQueryParams"
  ]) {
    if ((indicator >> i2++ & 1) === 1) {
      traits[trait] = 1;
    }
  }
  return traitsCache[indicator] = traits;
}

// node_modules/@smithy/core/dist-es/submodules/schema/schemas/NormalizedSchema.js
var anno = {
  it: /* @__PURE__ */ Symbol.for("@smithy/nor-struct-it"),
  ns: /* @__PURE__ */ Symbol.for("@smithy/ns")
};
var simpleSchemaCacheN = [];
var simpleSchemaCacheS = {};
var NormalizedSchema = class _NormalizedSchema {
  ref;
  memberName;
  static symbol = /* @__PURE__ */ Symbol.for("@smithy/nor");
  symbol = _NormalizedSchema.symbol;
  name;
  schema;
  _isMemberSchema;
  traits;
  memberTraits;
  normalizedTraits;
  constructor(ref, memberName) {
    this.ref = ref;
    this.memberName = memberName;
    const traitStack = [];
    let _ref = ref;
    let schema = ref;
    this._isMemberSchema = false;
    while (isMemberSchema(_ref)) {
      traitStack.push(_ref[1]);
      _ref = _ref[0];
      schema = deref(_ref);
      this._isMemberSchema = true;
    }
    if (traitStack.length > 0) {
      this.memberTraits = {};
      for (let i2 = traitStack.length - 1; i2 >= 0; --i2) {
        const traitSet = traitStack[i2];
        Object.assign(this.memberTraits, translateTraits(traitSet));
      }
    } else {
      this.memberTraits = 0;
    }
    if (schema instanceof _NormalizedSchema) {
      const computedMemberTraits = this.memberTraits;
      Object.assign(this, schema);
      this.memberTraits = Object.assign({}, computedMemberTraits, schema.getMemberTraits(), this.getMemberTraits());
      this.normalizedTraits = void 0;
      this.memberName = memberName ?? schema.memberName;
      return;
    }
    this.schema = deref(schema);
    if (isStaticSchema(this.schema)) {
      this.name = `${this.schema[1]}#${this.schema[2]}`;
      this.traits = this.schema[3];
    } else {
      this.name = this.memberName ?? String(schema);
      this.traits = 0;
    }
    if (this._isMemberSchema && !memberName) {
      throw new Error(`@smithy/core/schema - NormalizedSchema member init ${this.getName(true)} missing member name.`);
    }
  }
  static [Symbol.hasInstance](lhs) {
    const isPrototype = this.prototype.isPrototypeOf(lhs);
    if (!isPrototype && typeof lhs === "object" && lhs !== null) {
      const ns = lhs;
      return ns.symbol === this.symbol;
    }
    return isPrototype;
  }
  static of(ref) {
    const keyAble = typeof ref === "function" || typeof ref === "object" && ref !== null;
    if (typeof ref === "number") {
      if (simpleSchemaCacheN[ref]) {
        return simpleSchemaCacheN[ref];
      }
    } else if (typeof ref === "string") {
      if (simpleSchemaCacheS[ref]) {
        return simpleSchemaCacheS[ref];
      }
    } else if (keyAble) {
      if (ref[anno.ns]) {
        return ref[anno.ns];
      }
    }
    const sc = deref(ref);
    if (sc instanceof _NormalizedSchema) {
      return sc;
    }
    if (isMemberSchema(sc)) {
      const [ns2, traits] = sc;
      if (ns2 instanceof _NormalizedSchema) {
        Object.assign(ns2.getMergedTraits(), translateTraits(traits));
        return ns2;
      }
      throw new Error(`@smithy/core/schema - may not init unwrapped member schema=${JSON.stringify(ref, null, 2)}.`);
    }
    const ns = new _NormalizedSchema(sc);
    if (keyAble) {
      return ref[anno.ns] = ns;
    }
    if (typeof sc === "string") {
      return simpleSchemaCacheS[sc] = ns;
    }
    if (typeof sc === "number") {
      return simpleSchemaCacheN[sc] = ns;
    }
    return ns;
  }
  getSchema() {
    const sc = this.schema;
    if (Array.isArray(sc) && sc[0] === 0) {
      return sc[4];
    }
    return sc;
  }
  getName(withNamespace = false) {
    const { name } = this;
    const short = !withNamespace && name && name.includes("#");
    return short ? name.split("#")[1] : name || void 0;
  }
  getMemberName() {
    return this.memberName;
  }
  isMemberSchema() {
    return this._isMemberSchema;
  }
  isListSchema() {
    const sc = this.getSchema();
    return typeof sc === "number" ? sc >= 64 && sc < 128 : sc[0] === 1;
  }
  isMapSchema() {
    const sc = this.getSchema();
    return typeof sc === "number" ? sc >= 128 && sc <= 255 : sc[0] === 2;
  }
  isStructSchema() {
    const sc = this.getSchema();
    if (typeof sc !== "object") {
      return false;
    }
    const id = sc[0];
    return id === 3 || id === -3 || id === 4;
  }
  isUnionSchema() {
    const sc = this.getSchema();
    if (typeof sc !== "object") {
      return false;
    }
    return sc[0] === 4;
  }
  isBlobSchema() {
    const sc = this.getSchema();
    return sc === 21 || sc === 42;
  }
  isTimestampSchema() {
    const sc = this.getSchema();
    return typeof sc === "number" && sc >= 4 && sc <= 7;
  }
  isUnitSchema() {
    return this.getSchema() === "unit";
  }
  isDocumentSchema() {
    return this.getSchema() === 15;
  }
  isStringSchema() {
    return this.getSchema() === 0;
  }
  isBooleanSchema() {
    return this.getSchema() === 2;
  }
  isNumericSchema() {
    return this.getSchema() === 1;
  }
  isBigIntegerSchema() {
    return this.getSchema() === 17;
  }
  isBigDecimalSchema() {
    return this.getSchema() === 19;
  }
  isStreaming() {
    const { streaming } = this.getMergedTraits();
    return !!streaming || this.getSchema() === 42;
  }
  isIdempotencyToken() {
    return !!this.getMergedTraits().idempotencyToken;
  }
  getMergedTraits() {
    return this.normalizedTraits ?? (this.normalizedTraits = {
      ...this.getOwnTraits(),
      ...this.getMemberTraits()
    });
  }
  getMemberTraits() {
    return translateTraits(this.memberTraits);
  }
  getOwnTraits() {
    return translateTraits(this.traits);
  }
  getKeySchema() {
    const [isDoc, isMap] = [this.isDocumentSchema(), this.isMapSchema()];
    if (!isDoc && !isMap) {
      throw new Error(`@smithy/core/schema - cannot get key for non-map: ${this.getName(true)}`);
    }
    const schema = this.getSchema();
    const memberSchema = isDoc ? 15 : schema[4] ?? 0;
    return member([memberSchema, 0], "key");
  }
  getValueSchema() {
    const sc = this.getSchema();
    const [isDoc, isMap, isList] = [this.isDocumentSchema(), this.isMapSchema(), this.isListSchema()];
    const memberSchema = typeof sc === "number" ? 63 & sc : sc && typeof sc === "object" && (isMap || isList) ? sc[3 + sc[0]] : isDoc ? 15 : void 0;
    if (memberSchema != null) {
      return member([memberSchema, 0], isMap ? "value" : "member");
    }
    throw new Error(`@smithy/core/schema - ${this.getName(true)} has no value member.`);
  }
  getMemberSchema(memberName) {
    const struct = this.getSchema();
    if (this.isStructSchema() && struct[4].includes(memberName)) {
      const i2 = struct[4].indexOf(memberName);
      const memberSchema = struct[5][i2];
      return member(isMemberSchema(memberSchema) ? memberSchema : [memberSchema, 0], memberName);
    }
    if (this.isDocumentSchema()) {
      return member([15, 0], memberName);
    }
    throw new Error(`@smithy/core/schema - ${this.getName(true)} has no member=${memberName}.`);
  }
  getMemberSchemas() {
    const buffer = {};
    try {
      for (const [k2, v2] of this.structIterator()) {
        buffer[k2] = v2;
      }
    } catch (ignored) {
    }
    return buffer;
  }
  getEventStreamMember() {
    if (this.isStructSchema()) {
      for (const [memberName, memberSchema] of this.structIterator()) {
        if (memberSchema.isStreaming() && memberSchema.isStructSchema()) {
          return memberName;
        }
      }
    }
    return "";
  }
  *structIterator() {
    if (this.isUnitSchema()) {
      return;
    }
    if (!this.isStructSchema()) {
      throw new Error("@smithy/core/schema - cannot iterate non-struct schema.");
    }
    const struct = this.getSchema();
    const z = struct[4].length;
    let it = struct[anno.it];
    if (it && z === it.length) {
      yield* it;
      return;
    }
    it = Array(z);
    for (let i2 = 0; i2 < z; ++i2) {
      const k2 = struct[4][i2];
      const v2 = member([struct[5][i2], 0], k2);
      yield it[i2] = [k2, v2];
    }
    struct[anno.it] = it;
  }
};
function member(memberSchema, memberName) {
  if (memberSchema instanceof NormalizedSchema) {
    return Object.assign(memberSchema, {
      memberName,
      _isMemberSchema: true
    });
  }
  const internalCtorAccess = NormalizedSchema;
  return new internalCtorAccess(memberSchema, memberName);
}
var isMemberSchema = (sc) => Array.isArray(sc) && sc.length === 2;
var isStaticSchema = (sc) => Array.isArray(sc) && sc.length >= 5;

// node_modules/@smithy/core/dist-es/submodules/schema/TypeRegistry.js
var TypeRegistry = class _TypeRegistry {
  namespace;
  schemas;
  exceptions;
  static registries = /* @__PURE__ */ new Map();
  constructor(namespace, schemas = /* @__PURE__ */ new Map(), exceptions = /* @__PURE__ */ new Map()) {
    this.namespace = namespace;
    this.schemas = schemas;
    this.exceptions = exceptions;
  }
  static for(namespace) {
    if (!_TypeRegistry.registries.has(namespace)) {
      _TypeRegistry.registries.set(namespace, new _TypeRegistry(namespace));
    }
    return _TypeRegistry.registries.get(namespace);
  }
  copyFrom(other) {
    const { schemas, exceptions } = this;
    for (const [k2, v2] of other.schemas) {
      if (!schemas.has(k2)) {
        schemas.set(k2, v2);
      }
    }
    for (const [k2, v2] of other.exceptions) {
      if (!exceptions.has(k2)) {
        exceptions.set(k2, v2);
      }
    }
  }
  register(shapeId, schema) {
    const qualifiedName = this.normalizeShapeId(shapeId);
    for (const r2 of [this, _TypeRegistry.for(qualifiedName.split("#")[0])]) {
      r2.schemas.set(qualifiedName, schema);
    }
  }
  getSchema(shapeId) {
    const id = this.normalizeShapeId(shapeId);
    if (!this.schemas.has(id)) {
      if (!shapeId.includes("#")) {
        const suffix = "#" + shapeId;
        const candidates = [];
        for (const [shapeId2, schema] of this.schemas.entries()) {
          if (shapeId2.endsWith(suffix)) {
            candidates.push(schema);
          }
        }
        if (candidates.length === 1) {
          return candidates[0];
        }
      }
      throw new Error(`@smithy/core/schema - schema not found for ${id}`);
    }
    return this.schemas.get(id);
  }
  registerError(es, ctor) {
    const $error = es;
    const ns = $error[1];
    for (const r2 of [this, _TypeRegistry.for(ns)]) {
      r2.schemas.set(ns + "#" + $error[2], $error);
      r2.exceptions.set($error, ctor);
    }
  }
  getErrorCtor(es) {
    const $error = es;
    if (this.exceptions.has($error)) {
      return this.exceptions.get($error);
    }
    const registry = _TypeRegistry.for($error[1]);
    return registry.exceptions.get($error);
  }
  getBaseException() {
    for (const exceptionKey of this.exceptions.keys()) {
      if (Array.isArray(exceptionKey)) {
        const [, ns, name] = exceptionKey;
        const id = ns + "#" + name;
        if (id.startsWith("smithy.ts.sdk.synthetic.") && id.endsWith("ServiceException")) {
          return exceptionKey;
        }
      }
    }
    return void 0;
  }
  find(predicate) {
    for (const schema of this.schemas.values()) {
      if (predicate(schema)) {
        return schema;
      }
    }
    return void 0;
  }
  clear() {
    this.schemas.clear();
    this.exceptions.clear();
  }
  normalizeShapeId(shapeId) {
    if (shapeId.includes("#")) {
      return shapeId;
    }
    return this.namespace + "#" + shapeId;
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/HttpBindingProtocol.js
init_index_browser2();
init_transport();

// node_modules/@smithy/core/dist-es/submodules/protocols/HttpProtocol.js
init_transport();

// node_modules/@smithy/core/dist-es/submodules/protocols/SerdeContext.js
var SerdeContext = class {
  serdeContext;
  setSerdeContext(serdeContext) {
    this.serdeContext = serdeContext;
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/HttpProtocol.js
var HttpProtocol = class extends SerdeContext {
  options;
  compositeErrorRegistry;
  constructor(options) {
    super();
    this.options = options;
    this.compositeErrorRegistry = TypeRegistry.for(options.defaultNamespace);
    for (const etr of options.errorTypeRegistries ?? []) {
      this.compositeErrorRegistry.copyFrom(etr);
    }
  }
  getRequestType() {
    return HttpRequest;
  }
  getResponseType() {
    return HttpResponse;
  }
  setSerdeContext(serdeContext) {
    this.serdeContext = serdeContext;
    this.serializer.setSerdeContext(serdeContext);
    this.deserializer.setSerdeContext(serdeContext);
    if (this.getPayloadCodec()) {
      this.getPayloadCodec().setSerdeContext(serdeContext);
    }
  }
  updateServiceEndpoint(request, endpoint) {
    if ("url" in endpoint) {
      request.protocol = endpoint.url.protocol;
      request.hostname = endpoint.url.hostname;
      request.port = endpoint.url.port ? Number(endpoint.url.port) : void 0;
      request.path = endpoint.url.pathname;
      request.fragment = endpoint.url.hash || void 0;
      request.username = endpoint.url.username || void 0;
      request.password = endpoint.url.password || void 0;
      if (!request.query) {
        request.query = {};
      }
      for (const [k2, v2] of endpoint.url.searchParams.entries()) {
        request.query[k2] = v2;
      }
      if (endpoint.headers) {
        for (const name in endpoint.headers) {
          request.headers[name] = endpoint.headers[name].join(", ");
        }
      }
      return request;
    } else {
      request.protocol = endpoint.protocol;
      request.hostname = endpoint.hostname;
      request.port = endpoint.port ? Number(endpoint.port) : void 0;
      request.path = endpoint.path;
      request.query = {
        ...endpoint.query
      };
      if (endpoint.headers) {
        for (const name in endpoint.headers) {
          request.headers[name] = endpoint.headers[name];
        }
      }
      return request;
    }
  }
  setHostPrefix(request, operationSchema, input) {
    if (this.serdeContext?.disableHostPrefix) {
      return;
    }
    const inputNs = NormalizedSchema.of(operationSchema.input);
    const opTraits = translateTraits(operationSchema.traits ?? {});
    if (opTraits.endpoint) {
      let hostPrefix = opTraits.endpoint?.[0];
      if (typeof hostPrefix === "string") {
        for (const [name, member2] of inputNs.structIterator()) {
          if (!member2.getMergedTraits().hostLabel) {
            continue;
          }
          const replacement = input[name];
          if (typeof replacement !== "string") {
            throw new Error(`@smithy/core/schema - ${name} in input must be a string as hostLabel.`);
          }
          hostPrefix = hostPrefix.replace(`{${name}}`, replacement);
        }
        request.hostname = hostPrefix + request.hostname;
        if (!isValidHostname(request.hostname)) {
          throw new Error(`[${request.hostname}] is not a valid hostname.`);
        }
      }
    }
  }
  deserializeMetadata(output) {
    return {
      httpStatusCode: output.statusCode,
      requestId: output.headers["x-amzn-requestid"] ?? output.headers["x-amzn-request-id"] ?? output.headers["x-amz-request-id"],
      extendedRequestId: output.headers["x-amz-id-2"],
      cfId: output.headers["x-amz-cf-id"]
    };
  }
  async serializeEventStream({ eventStream, requestSchema, initialRequest }) {
    const eventStreamSerde = await this.loadEventStreamCapability();
    return eventStreamSerde.serializeEventStream({
      eventStream,
      requestSchema,
      initialRequest
    });
  }
  async deserializeEventStream({ response, responseSchema, initialResponseContainer }) {
    const eventStreamSerde = await this.loadEventStreamCapability();
    return eventStreamSerde.deserializeEventStream({
      response,
      responseSchema,
      initialResponseContainer
    });
  }
  async loadEventStreamCapability() {
    const { EventStreamSerde: EventStreamSerde2, eventStreamSerdeProvider: eventStreamSerdeProvider3 } = await Promise.resolve().then(() => (init_index_browser4(), index_browser_exports));
    const marshaller = this.resolveEventStreamMarshaller(eventStreamSerdeProvider3);
    return new EventStreamSerde2({
      marshaller,
      serializer: this.serializer,
      deserializer: this.deserializer,
      serdeContext: this.serdeContext,
      defaultContentType: this.getDefaultContentType()
    });
  }
  resolveEventStreamMarshaller(importedProvider) {
    const context = this.serdeContext;
    if (context.eventStreamMarshaller) {
      return context.eventStreamMarshaller;
    }
    return importedProvider(this.serdeContext);
  }
  getDefaultContentType() {
    throw new Error(`@smithy/core/protocols - ${this.constructor.name} getDefaultContentType() implementation missing.`);
  }
  async deserializeHttpMessage(schema, context, response, arg4, arg5) {
    void schema;
    void context;
    void response;
    void arg4;
    void arg5;
    return [];
  }
  getEventStreamMarshaller() {
    const context = this.serdeContext;
    if (!context.eventStreamMarshaller) {
      throw new Error("@smithy/core - HttpProtocol: eventStreamMarshaller missing in serdeContext.");
    }
    return context.eventStreamMarshaller;
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/HttpBindingProtocol.js
var HttpBindingProtocol = class extends HttpProtocol {
  async serializeRequest(operationSchema, _input, context) {
    const input = _input && typeof _input === "object" ? _input : {};
    const serializer = this.serializer;
    const query = {};
    const headers = {};
    const endpoint = await context.endpoint();
    const ns = NormalizedSchema.of(operationSchema?.input);
    const payloadMemberNames = [];
    const payloadMemberSchemas = [];
    let hasNonHttpBindingMember = false;
    let payload;
    const request = new HttpRequest({
      protocol: "",
      hostname: "",
      port: void 0,
      path: "",
      fragment: void 0,
      query,
      headers,
      body: void 0
    });
    if (endpoint) {
      this.updateServiceEndpoint(request, endpoint);
      this.setHostPrefix(request, operationSchema, input);
      const opTraits = translateTraits(operationSchema.traits);
      if (opTraits.http) {
        request.method = opTraits.http[0];
        const [path, search] = opTraits.http[1].split("?");
        if (request.path == "/") {
          request.path = path;
        } else {
          request.path += path;
        }
        const traitSearchParams = new URLSearchParams(search ?? "");
        for (const [key, value] of traitSearchParams) {
          query[key] = value;
        }
      }
    }
    for (const [memberName, memberNs] of ns.structIterator()) {
      const memberTraits = memberNs.getMergedTraits() ?? {};
      const inputMemberValue = input[memberName];
      if (inputMemberValue == null && !memberNs.isIdempotencyToken()) {
        if (memberTraits.httpLabel) {
          if (request.path.includes(`{${memberName}+}`) || request.path.includes(`{${memberName}}`)) {
            throw new Error(`No value provided for input HTTP label: ${memberName}.`);
          }
        }
        continue;
      }
      if (memberTraits.httpPayload) {
        const isStreaming = memberNs.isStreaming();
        if (isStreaming) {
          const isEventStream = memberNs.isStructSchema();
          if (isEventStream) {
            if (input[memberName]) {
              payload = await this.serializeEventStream({
                eventStream: input[memberName],
                requestSchema: ns
              });
            }
          } else {
            payload = inputMemberValue;
          }
        } else {
          serializer.write(memberNs, inputMemberValue);
          payload = serializer.flush();
        }
      } else if (memberTraits.httpLabel) {
        serializer.write(memberNs, inputMemberValue);
        const replacement = serializer.flush();
        if (request.path.includes(`{${memberName}+}`)) {
          request.path = request.path.replace(`{${memberName}+}`, replacement.split("/").map(extendedEncodeURIComponent).join("/"));
        } else if (request.path.includes(`{${memberName}}`)) {
          request.path = request.path.replace(`{${memberName}}`, extendedEncodeURIComponent(replacement));
        }
      } else if (memberTraits.httpHeader) {
        serializer.write(memberNs, inputMemberValue);
        headers[memberTraits.httpHeader.toLowerCase()] = String(serializer.flush());
      } else if (typeof memberTraits.httpPrefixHeaders === "string") {
        for (const key in inputMemberValue) {
          const val = inputMemberValue[key];
          const amalgam = memberTraits.httpPrefixHeaders + key;
          serializer.write([memberNs.getValueSchema(), { httpHeader: amalgam }], val);
          headers[amalgam.toLowerCase()] = serializer.flush();
        }
      } else if (memberTraits.httpQuery || memberTraits.httpQueryParams) {
        this.serializeQuery(memberNs, inputMemberValue, query);
      } else {
        hasNonHttpBindingMember = true;
        payloadMemberNames.push(memberName);
        payloadMemberSchemas.push(memberNs);
      }
    }
    if (hasNonHttpBindingMember && input) {
      const [namespace, name] = (ns.getName(true) ?? "#Unknown").split("#");
      const requiredMembers = ns.getSchema()[6];
      const payloadSchema = [
        3,
        namespace,
        name,
        ns.getMergedTraits(),
        payloadMemberNames,
        payloadMemberSchemas,
        void 0
      ];
      if (requiredMembers) {
        payloadSchema[6] = requiredMembers;
      } else {
        payloadSchema.pop();
      }
      serializer.write(payloadSchema, input);
      payload = serializer.flush();
    }
    request.headers = headers;
    request.query = query;
    request.body = payload;
    return request;
  }
  serializeQuery(ns, data, query) {
    const serializer = this.serializer;
    const traits = ns.getMergedTraits();
    if (traits.httpQueryParams) {
      for (const key in data) {
        if (!(key in query)) {
          const val = data[key];
          const valueSchema = ns.getValueSchema();
          Object.assign(valueSchema.getMergedTraits(), {
            ...traits,
            httpQuery: key,
            httpQueryParams: void 0
          });
          this.serializeQuery(valueSchema, val, query);
        }
      }
      return;
    }
    if (ns.isListSchema()) {
      const sparse = !!ns.getMergedTraits().sparse;
      const buffer = [];
      for (const item of data) {
        serializer.write([ns.getValueSchema(), traits], item);
        const serializable = serializer.flush();
        if (sparse || serializable !== void 0) {
          buffer.push(serializable);
        }
      }
      query[traits.httpQuery] = buffer;
    } else {
      serializer.write([ns, traits], data);
      query[traits.httpQuery] = serializer.flush();
    }
  }
  async deserializeResponse(operationSchema, context, response) {
    const deserializer = this.deserializer;
    const ns = NormalizedSchema.of(operationSchema.output);
    const dataObject = {};
    if (response.statusCode >= 300) {
      const bytes = await collectBody(response.body, context);
      if (bytes.byteLength > 0) {
        Object.assign(dataObject, await deserializer.read(15, bytes));
      }
      await this.handleError(operationSchema, context, response, dataObject, this.deserializeMetadata(response));
      throw new Error("@smithy/core/protocols - HTTP Protocol error handler failed to throw.");
    }
    for (const header in response.headers) {
      const value = response.headers[header];
      delete response.headers[header];
      response.headers[header.toLowerCase()] = value;
    }
    const nonHttpBindingMembers = await this.deserializeHttpMessage(ns, context, response, dataObject);
    if (nonHttpBindingMembers.length) {
      const bytes = await collectBody(response.body, context);
      if (bytes.byteLength > 0) {
        const dataFromBody = await deserializer.read(ns, bytes);
        for (const member2 of nonHttpBindingMembers) {
          if (dataFromBody[member2] != null) {
            dataObject[member2] = dataFromBody[member2];
          }
        }
      }
    } else if (nonHttpBindingMembers.discardResponseBody) {
      await collectBody(response.body, context);
    }
    dataObject.$metadata = this.deserializeMetadata(response);
    return dataObject;
  }
  async deserializeHttpMessage(schema, context, response, arg4, arg5) {
    let dataObject;
    if (arg4 instanceof Set) {
      dataObject = arg5;
    } else {
      dataObject = arg4;
    }
    let discardResponseBody = true;
    const deserializer = this.deserializer;
    const ns = NormalizedSchema.of(schema);
    const nonHttpBindingMembers = [];
    for (const [memberName, memberSchema] of ns.structIterator()) {
      const memberTraits = memberSchema.getMemberTraits();
      if (memberTraits.httpPayload) {
        discardResponseBody = false;
        const isStreaming = memberSchema.isStreaming();
        if (isStreaming) {
          const isEventStream = memberSchema.isStructSchema();
          if (isEventStream) {
            dataObject[memberName] = await this.deserializeEventStream({
              response,
              responseSchema: ns
            });
          } else {
            dataObject[memberName] = sdkStreamMixin(response.body);
          }
        } else if (response.body) {
          const bytes = await collectBody(response.body, context);
          if (bytes.byteLength > 0) {
            dataObject[memberName] = await deserializer.read(memberSchema, bytes);
          }
        }
      } else if (memberTraits.httpHeader) {
        const key = String(memberTraits.httpHeader).toLowerCase();
        const value = response.headers[key];
        if (null != value) {
          if (memberSchema.isListSchema()) {
            const headerListValueSchema = memberSchema.getValueSchema();
            headerListValueSchema.getMergedTraits().httpHeader = key;
            let sections;
            if (headerListValueSchema.isTimestampSchema() && headerListValueSchema.getSchema() === 4) {
              sections = splitEvery(value, ",", 2);
            } else {
              sections = splitHeader(value);
            }
            const list = [];
            for (const section of sections) {
              list.push(await deserializer.read(headerListValueSchema, section.trim()));
            }
            dataObject[memberName] = list;
          } else {
            dataObject[memberName] = await deserializer.read(memberSchema, value);
          }
        }
      } else if (memberTraits.httpPrefixHeaders !== void 0) {
        dataObject[memberName] = {};
        for (const header in response.headers) {
          if (header.startsWith(memberTraits.httpPrefixHeaders)) {
            const value = response.headers[header];
            const valueSchema = memberSchema.getValueSchema();
            valueSchema.getMergedTraits().httpHeader = header;
            dataObject[memberName][header.slice(memberTraits.httpPrefixHeaders.length)] = await deserializer.read(valueSchema, value);
          }
        }
      } else if (memberTraits.httpResponseCode) {
        dataObject[memberName] = response.statusCode;
      } else {
        nonHttpBindingMembers.push(memberName);
      }
    }
    nonHttpBindingMembers.discardResponseBody = discardResponseBody;
    return nonHttpBindingMembers;
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/serde/FromStringShapeDeserializer.js
init_index_browser2();

// node_modules/@smithy/core/dist-es/submodules/protocols/serde/determineTimestampFormat.js
function determineTimestampFormat(ns, settings) {
  if (settings.timestampFormat.useTrait) {
    if (ns.isTimestampSchema() && (ns.getSchema() === 5 || ns.getSchema() === 6 || ns.getSchema() === 7)) {
      return ns.getSchema();
    }
  }
  const { httpLabel, httpPrefixHeaders, httpHeader, httpQuery } = ns.getMergedTraits();
  const bindingFormat = settings.httpBindings ? typeof httpPrefixHeaders === "string" || Boolean(httpHeader) ? 6 : Boolean(httpQuery) || Boolean(httpLabel) ? 5 : void 0 : void 0;
  return bindingFormat ?? settings.timestampFormat.default;
}

// node_modules/@smithy/core/dist-es/submodules/protocols/serde/FromStringShapeDeserializer.js
var FromStringShapeDeserializer = class extends SerdeContext {
  settings;
  constructor(settings) {
    super();
    this.settings = settings;
  }
  read(_schema, data) {
    const ns = NormalizedSchema.of(_schema);
    if (ns.isListSchema()) {
      return splitHeader(data).map((item) => this.read(ns.getValueSchema(), item));
    }
    if (ns.isBlobSchema()) {
      return (this.serdeContext?.base64Decoder ?? fromBase64)(data);
    }
    if (ns.isTimestampSchema()) {
      const format2 = determineTimestampFormat(ns, this.settings);
      switch (format2) {
        case 5:
          return _parseRfc3339DateTimeWithOffset(data);
        case 6:
          return _parseRfc7231DateTime(data);
        case 7:
          return _parseEpochTimestamp(data);
        default:
          console.warn("Missing timestamp format, parsing value with Date constructor:", data);
          return new Date(data);
      }
    }
    if (ns.isStringSchema()) {
      const mediaType = ns.getMergedTraits().mediaType;
      let intermediateValue = data;
      if (mediaType) {
        if (ns.getMergedTraits().httpHeader) {
          intermediateValue = this.base64ToUtf8(intermediateValue);
        }
        const isJson = mediaType === "application/json" || mediaType.endsWith("+json");
        if (isJson) {
          intermediateValue = LazyJsonString.from(intermediateValue);
        }
        return intermediateValue;
      }
    }
    if (ns.isNumericSchema()) {
      return Number(data);
    }
    if (ns.isBigIntegerSchema()) {
      return BigInt(data);
    }
    if (ns.isBigDecimalSchema()) {
      return new NumericValue(data, "bigDecimal");
    }
    if (ns.isBooleanSchema()) {
      return String(data).toLowerCase() === "true";
    }
    return data;
  }
  base64ToUtf8(base64String) {
    return (this.serdeContext?.utf8Encoder ?? toUtf8)((this.serdeContext?.base64Decoder ?? fromBase64)(base64String));
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/serde/HttpInterceptingShapeDeserializer.js
init_index_browser2();
var HttpInterceptingShapeDeserializer = class extends SerdeContext {
  codecDeserializer;
  stringDeserializer;
  constructor(codecDeserializer, codecSettings) {
    super();
    this.codecDeserializer = codecDeserializer;
    this.stringDeserializer = new FromStringShapeDeserializer(codecSettings);
  }
  setSerdeContext(serdeContext) {
    this.stringDeserializer.setSerdeContext(serdeContext);
    this.codecDeserializer.setSerdeContext(serdeContext);
    this.serdeContext = serdeContext;
  }
  read(schema, data) {
    const ns = NormalizedSchema.of(schema);
    const traits = ns.getMergedTraits();
    const toString = this.serdeContext?.utf8Encoder ?? toUtf8;
    if (traits.httpHeader || traits.httpResponseCode) {
      return this.stringDeserializer.read(ns, toString(data));
    }
    if (traits.httpPayload) {
      if (ns.isBlobSchema()) {
        const toBytes = this.serdeContext?.utf8Decoder ?? fromUtf8;
        if (typeof data === "string") {
          return toBytes(data);
        }
        return data;
      } else if (ns.isStringSchema()) {
        if ("byteLength" in data) {
          return toString(data);
        }
        return data;
      }
    }
    return this.codecDeserializer.read(ns, data);
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/serde/ToStringShapeSerializer.js
init_index_browser2();
var ToStringShapeSerializer = class extends SerdeContext {
  settings;
  stringBuffer = "";
  constructor(settings) {
    super();
    this.settings = settings;
  }
  write(schema, value) {
    const ns = NormalizedSchema.of(schema);
    switch (typeof value) {
      case "object":
        if (value === null) {
          this.stringBuffer = "null";
          return;
        }
        if (ns.isTimestampSchema()) {
          if (!(value instanceof Date)) {
            throw new Error(`@smithy/core/protocols - received non-Date value ${value} when schema expected Date in ${ns.getName(true)}`);
          }
          const format2 = determineTimestampFormat(ns, this.settings);
          switch (format2) {
            case 5:
              this.stringBuffer = value.toISOString().replace(".000Z", "Z");
              break;
            case 6:
              this.stringBuffer = dateToUtcString(value);
              break;
            case 7:
              this.stringBuffer = String(value.getTime() / 1e3);
              break;
            default:
              console.warn("Missing timestamp format, using epoch seconds", value);
              this.stringBuffer = String(value.getTime() / 1e3);
          }
          return;
        }
        if (ns.isBlobSchema() && "byteLength" in value) {
          this.stringBuffer = (this.serdeContext?.base64Encoder ?? toBase64)(value);
          return;
        }
        if (ns.isListSchema() && Array.isArray(value)) {
          let buffer = "";
          for (const item of value) {
            this.write([ns.getValueSchema(), ns.getMergedTraits()], item);
            const headerItem = this.flush();
            const serialized = ns.getValueSchema().isTimestampSchema() ? headerItem : quoteHeader(headerItem);
            if (buffer !== "") {
              buffer += ", ";
            }
            buffer += serialized;
          }
          this.stringBuffer = buffer;
          return;
        }
        this.stringBuffer = JSON.stringify(value, null, 2);
        break;
      case "string":
        const mediaType = ns.getMergedTraits().mediaType;
        let intermediateValue = value;
        if (mediaType) {
          const isJson = mediaType === "application/json" || mediaType.endsWith("+json");
          if (isJson) {
            intermediateValue = LazyJsonString.from(intermediateValue);
          }
          if (ns.getMergedTraits().httpHeader) {
            this.stringBuffer = (this.serdeContext?.base64Encoder ?? toBase64)(intermediateValue.toString());
            return;
          }
        }
        this.stringBuffer = value;
        break;
      default:
        if (ns.isIdempotencyToken()) {
          this.stringBuffer = generateIdempotencyToken();
        } else {
          this.stringBuffer = String(value);
        }
    }
  }
  flush() {
    const buffer = this.stringBuffer;
    this.stringBuffer = "";
    return buffer;
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/serde/HttpInterceptingShapeSerializer.js
var HttpInterceptingShapeSerializer = class {
  codecSerializer;
  stringSerializer;
  buffer;
  constructor(codecSerializer, codecSettings, stringSerializer = new ToStringShapeSerializer(codecSettings)) {
    this.codecSerializer = codecSerializer;
    this.stringSerializer = stringSerializer;
  }
  setSerdeContext(serdeContext) {
    this.codecSerializer.setSerdeContext(serdeContext);
    this.stringSerializer.setSerdeContext(serdeContext);
  }
  write(schema, value) {
    const ns = NormalizedSchema.of(schema);
    const traits = ns.getMergedTraits();
    if (traits.httpHeader || traits.httpLabel || traits.httpQuery) {
      this.stringSerializer.write(ns, value);
      this.buffer = this.stringSerializer.flush();
      return;
    }
    return this.codecSerializer.write(ns, value);
  }
  flush() {
    if (this.buffer !== void 0) {
      const buffer = this.buffer;
      this.buffer = void 0;
      return buffer;
    }
    return this.codecSerializer.flush();
  }
};

// node_modules/@smithy/core/dist-es/submodules/protocols/index.js
init_transport();
init_transport();

// node_modules/@smithy/core/dist-es/submodules/protocols/protocol-http/extensions/httpExtensionConfiguration.js
var getHttpHandlerExtensionConfiguration = (runtimeConfig) => {
  return {
    setHttpHandler(handler) {
      runtimeConfig.httpHandler = handler;
    },
    httpHandler() {
      return runtimeConfig.httpHandler;
    },
    updateHttpClientConfig(key, value) {
      runtimeConfig.httpHandler?.updateHttpClientConfig(key, value);
    },
    httpHandlerConfigs() {
      return runtimeConfig.httpHandler.httpHandlerConfigs();
    }
  };
};
var resolveHttpHandlerRuntimeConfig = (httpHandlerExtensionConfiguration) => {
  return {
    httpHandler: httpHandlerExtensionConfiguration.httpHandler()
  };
};

// node_modules/@smithy/core/dist-es/submodules/protocols/middleware-content-length/contentLengthMiddleware.js
init_transport();
var CONTENT_LENGTH_HEADER = "content-length";
function contentLengthMiddleware(bodyLengthChecker) {
  return (next) => async (args) => {
    const request = args.request;
    if (HttpRequest.isInstance(request)) {
      const { body, headers } = request;
      if (body && Object.keys(headers).map((str) => str.toLowerCase()).indexOf(CONTENT_LENGTH_HEADER) === -1) {
        try {
          const length = bodyLengthChecker(body);
          request.headers = {
            ...request.headers,
            [CONTENT_LENGTH_HEADER]: String(length)
          };
        } catch (error) {
        }
      }
    }
    return next({
      ...args,
      request
    });
  };
}
var contentLengthMiddlewareOptions = {
  step: "build",
  tags: ["SET_CONTENT_LENGTH", "CONTENT_LENGTH"],
  name: "contentLengthMiddleware",
  override: true
};
var getContentLengthPlugin = (options) => ({
  applyToStack: (clientStack) => {
    clientStack.add(contentLengthMiddleware(options.bodyLengthChecker), contentLengthMiddlewareOptions);
  }
});

// node_modules/@smithy/core/dist-es/submodules/protocols/util-uri-escape/escape-uri.js
var escapeUri = (uri) => encodeURIComponent(uri).replace(/[!'()*]/g, hexEncode);
var hexEncode = (c2) => `%${c2.charCodeAt(0).toString(16).toUpperCase()}`;

// node_modules/@smithy/core/dist-es/submodules/protocols/querystring-builder/buildQueryString.js
function buildQueryString(query) {
  const parts = [];
  for (let key of Object.keys(query).sort()) {
    const value = query[key];
    key = escapeUri(key);
    if (Array.isArray(value)) {
      for (let i2 = 0, iLen = value.length; i2 < iLen; i2++) {
        parts.push(`${key}=${escapeUri(value[i2])}`);
      }
    } else {
      let qsEntry = key;
      if (value || typeof value === "string") {
        qsEntry += `=${escapeUri(value)}`;
      }
      parts.push(qsEntry);
    }
  }
  return parts.join("&");
}

// node_modules/@smithy/core/dist-es/submodules/protocols/index.js
init_transport();

// node_modules/@aws-sdk/middleware-host-header/dist-es/index.js
function resolveHostHeaderConfig(input) {
  return input;
}
var hostHeaderMiddleware = (options) => (next) => async (args) => {
  if (!HttpRequest.isInstance(args.request))
    return next(args);
  const { request } = args;
  const { handlerProtocol = "" } = options.requestHandler.metadata || {};
  if (handlerProtocol.indexOf("h2") >= 0 && !request.headers[":authority"]) {
    delete request.headers["host"];
    request.headers[":authority"] = request.hostname + (request.port ? ":" + request.port : "");
  } else if (!request.headers["host"]) {
    let host = request.hostname;
    if (request.port != null)
      host += `:${request.port}`;
    request.headers["host"] = host;
  }
  return next(args);
};
var hostHeaderMiddlewareOptions = {
  name: "hostHeaderMiddleware",
  step: "build",
  priority: "low",
  tags: ["HOST"],
  override: true
};
var getHostHeaderPlugin = (options) => ({
  applyToStack: (clientStack) => {
    clientStack.add(hostHeaderMiddleware(options), hostHeaderMiddlewareOptions);
  }
});

// node_modules/@aws-sdk/middleware-logger/dist-es/loggerMiddleware.js
var loggerMiddleware = () => (next, context) => async (args) => {
  try {
    const response = await next(args);
    const { clientName, commandName, logger: logger2, dynamoDbDocumentClientOptions = {} } = context;
    const { overrideInputFilterSensitiveLog, overrideOutputFilterSensitiveLog } = dynamoDbDocumentClientOptions;
    const inputFilterSensitiveLog = overrideInputFilterSensitiveLog ?? context.inputFilterSensitiveLog;
    const outputFilterSensitiveLog = overrideOutputFilterSensitiveLog ?? context.outputFilterSensitiveLog;
    const { $metadata, ...outputWithoutMetadata } = response.output;
    logger2?.info?.({
      clientName,
      commandName,
      input: inputFilterSensitiveLog(args.input),
      output: outputFilterSensitiveLog(outputWithoutMetadata),
      metadata: $metadata
    });
    return response;
  } catch (error) {
    const { clientName, commandName, logger: logger2, dynamoDbDocumentClientOptions = {} } = context;
    const { overrideInputFilterSensitiveLog } = dynamoDbDocumentClientOptions;
    const inputFilterSensitiveLog = overrideInputFilterSensitiveLog ?? context.inputFilterSensitiveLog;
    logger2?.error?.({
      clientName,
      commandName,
      input: inputFilterSensitiveLog(args.input),
      error,
      metadata: error.$metadata
    });
    throw error;
  }
};
var loggerMiddlewareOptions = {
  name: "loggerMiddleware",
  tags: ["LOGGER"],
  step: "initialize",
  override: true
};
var getLoggerPlugin = (options) => ({
  applyToStack: (clientStack) => {
    clientStack.add(loggerMiddleware(), loggerMiddlewareOptions);
  }
});

// node_modules/@aws-sdk/middleware-recursion-detection/dist-es/configuration.js
var recursionDetectionMiddlewareOptions = {
  step: "build",
  tags: ["RECURSION_DETECTION"],
  name: "recursionDetectionMiddleware",
  override: true,
  priority: "low"
};

// node_modules/@aws-sdk/middleware-recursion-detection/dist-es/recursionDetectionMiddleware.browser.js
var recursionDetectionMiddleware = () => (next) => async (args) => next(args);

// node_modules/@aws-sdk/middleware-recursion-detection/dist-es/getRecursionDetectionPlugin.js
var getRecursionDetectionPlugin = (options) => ({
  applyToStack: (clientStack) => {
    clientStack.add(recursionDetectionMiddleware(), recursionDetectionMiddlewareOptions);
  }
});

// node_modules/@smithy/core/dist-es/legacy-root-exports/middleware-http-auth-scheme/httpAuthSchemeMiddleware.js
init_transport();

// node_modules/@smithy/core/dist-es/legacy-root-exports/middleware-http-auth-scheme/resolveAuthOptions.js
var resolveAuthOptions = (candidateAuthOptions, authSchemePreference) => {
  if (!authSchemePreference || authSchemePreference.length === 0) {
    return candidateAuthOptions;
  }
  const preferredAuthOptions = [];
  for (const preferredSchemeName of authSchemePreference) {
    for (const candidateAuthOption of candidateAuthOptions) {
      const candidateAuthSchemeName = candidateAuthOption.schemeId.split("#")[1];
      if (candidateAuthSchemeName === preferredSchemeName) {
        preferredAuthOptions.push(candidateAuthOption);
      }
    }
  }
  for (const candidateAuthOption of candidateAuthOptions) {
    if (!preferredAuthOptions.find(({ schemeId }) => schemeId === candidateAuthOption.schemeId)) {
      preferredAuthOptions.push(candidateAuthOption);
    }
  }
  return preferredAuthOptions;
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/middleware-http-auth-scheme/httpAuthSchemeMiddleware.js
function convertHttpAuthSchemesToMap(httpAuthSchemes) {
  const map2 = /* @__PURE__ */ new Map();
  for (const scheme of httpAuthSchemes) {
    map2.set(scheme.schemeId, scheme);
  }
  return map2;
}
var httpAuthSchemeMiddleware = (config, mwOptions) => (next, context) => async (args) => {
  const options = config.httpAuthSchemeProvider(await mwOptions.httpAuthSchemeParametersProvider(config, context, args.input));
  const authSchemePreference = config.authSchemePreference ? await config.authSchemePreference() : [];
  const resolvedOptions = resolveAuthOptions(options, authSchemePreference);
  const authSchemes = convertHttpAuthSchemesToMap(config.httpAuthSchemes);
  const smithyContext = getSmithyContext(context);
  const failureReasons = [];
  for (const option of resolvedOptions) {
    const scheme = authSchemes.get(option.schemeId);
    if (!scheme) {
      failureReasons.push(`HttpAuthScheme \`${option.schemeId}\` was not enabled for this service.`);
      continue;
    }
    const identityProvider = scheme.identityProvider(await mwOptions.identityProviderConfigProvider(config));
    if (!identityProvider) {
      failureReasons.push(`HttpAuthScheme \`${option.schemeId}\` did not have an IdentityProvider configured.`);
      continue;
    }
    const { identityProperties = {}, signingProperties = {} } = option.propertiesExtractor?.(config, context) || {};
    option.identityProperties = Object.assign(option.identityProperties || {}, identityProperties);
    option.signingProperties = Object.assign(option.signingProperties || {}, signingProperties);
    smithyContext.selectedHttpAuthScheme = {
      httpAuthOption: option,
      identity: await identityProvider(option.identityProperties),
      signer: scheme.signer
    };
    break;
  }
  if (!smithyContext.selectedHttpAuthScheme) {
    throw new Error(failureReasons.join("\n"));
  }
  return next(args);
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/middleware-http-auth-scheme/getHttpAuthSchemeEndpointRuleSetPlugin.js
var httpAuthSchemeEndpointRuleSetMiddlewareOptions = {
  step: "serialize",
  tags: ["HTTP_AUTH_SCHEME"],
  name: "httpAuthSchemeMiddleware",
  override: true,
  relation: "before",
  toMiddleware: "endpointV2Middleware"
};
var getHttpAuthSchemeEndpointRuleSetPlugin = (config, { httpAuthSchemeParametersProvider, identityProviderConfigProvider }) => ({
  applyToStack: (clientStack) => {
    clientStack.addRelativeTo(httpAuthSchemeMiddleware(config, {
      httpAuthSchemeParametersProvider,
      identityProviderConfigProvider
    }), httpAuthSchemeEndpointRuleSetMiddlewareOptions);
  }
});

// node_modules/@smithy/core/dist-es/legacy-root-exports/middleware-http-signing/httpSigningMiddleware.js
init_transport();
var defaultErrorHandler = (signingProperties) => (error) => {
  throw error;
};
var defaultSuccessHandler = (httpResponse, signingProperties) => {
};
var httpSigningMiddleware = (config) => (next, context) => async (args) => {
  if (!HttpRequest.isInstance(args.request)) {
    return next(args);
  }
  const smithyContext = getSmithyContext(context);
  const scheme = smithyContext.selectedHttpAuthScheme;
  if (!scheme) {
    throw new Error(`No HttpAuthScheme was selected: unable to sign request`);
  }
  const { httpAuthOption: { signingProperties = {} }, identity, signer } = scheme;
  const output = await next({
    ...args,
    request: await signer.sign(args.request, identity, signingProperties)
  }).catch((signer.errorHandler || defaultErrorHandler)(signingProperties));
  (signer.successHandler || defaultSuccessHandler)(output.response, signingProperties);
  return output;
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/middleware-http-signing/getHttpSigningMiddleware.js
var httpSigningMiddlewareOptions = {
  step: "finalizeRequest",
  tags: ["HTTP_SIGNING"],
  name: "httpSigningMiddleware",
  aliases: ["apiKeyMiddleware", "tokenMiddleware", "awsAuthMiddleware"],
  override: true,
  relation: "after",
  toMiddleware: "retryMiddleware"
};
var getHttpSigningPlugin = (config) => ({
  applyToStack: (clientStack) => {
    clientStack.addRelativeTo(httpSigningMiddleware(config), httpSigningMiddlewareOptions);
  }
});

// node_modules/@smithy/core/dist-es/normalizeProvider.js
var normalizeProvider2 = (input) => {
  if (typeof input === "function")
    return input;
  const promisified = Promise.resolve(input);
  return () => promisified;
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/pagination/createPaginator.js
var makePagedClientRequest = async (CommandCtor, client, input, withCommand = (_) => _, ...args) => {
  let command = new CommandCtor(input);
  command = withCommand(command) ?? command;
  return await client.send(command, ...args);
};
function createPaginator(ClientCtor, CommandCtor, inputTokenName, outputTokenName, pageSizeTokenName) {
  return async function* paginateOperation(config, input, ...additionalArguments) {
    const _input = input;
    let token = config.startingToken ?? _input[inputTokenName];
    let hasNext = true;
    let page;
    while (hasNext) {
      _input[inputTokenName] = token;
      if (pageSizeTokenName) {
        _input[pageSizeTokenName] = _input[pageSizeTokenName] ?? config.pageSize;
      }
      if (config.client instanceof ClientCtor) {
        page = await makePagedClientRequest(CommandCtor, config.client, input, config.withCommand, ...additionalArguments);
      } else {
        throw new Error(`Invalid client, expected instance of ${ClientCtor.name}`);
      }
      yield page;
      const prevToken = token;
      token = get(page, outputTokenName);
      hasNext = !!(token && (!config.stopOnSameToken || token !== prevToken));
    }
    return void 0;
  };
}
var get = (fromObject, path) => {
  let cursor = fromObject;
  const pathComponents = path.split(".");
  for (const step of pathComponents) {
    if (!cursor || typeof cursor !== "object") {
      return void 0;
    }
    cursor = cursor[step];
  }
  return cursor;
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/util-identity-and-auth/DefaultIdentityProviderConfig.js
var DefaultIdentityProviderConfig = class {
  authSchemes = /* @__PURE__ */ new Map();
  constructor(config) {
    for (const key in config) {
      const value = config[key];
      if (value !== void 0) {
        this.authSchemes.set(key, value);
      }
    }
  }
  getIdentityProvider(schemeId) {
    return this.authSchemes.get(schemeId);
  }
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/util-identity-and-auth/httpAuthSchemes/httpBearerAuth.js
var HttpBearerAuthSigner = class {
  async sign(httpRequest, identity, signingProperties) {
    const clonedRequest = HttpRequest.clone(httpRequest);
    if (!identity.token) {
      throw new Error("request could not be signed with `token` since the `token` is not defined");
    }
    clonedRequest.headers["Authorization"] = `Bearer ${identity.token}`;
    return clonedRequest;
  }
};

// node_modules/@smithy/core/dist-es/legacy-root-exports/util-identity-and-auth/memoizeIdentityProvider.js
var createIsIdentityExpiredFunction = (expirationMs) => function isIdentityExpired2(identity) {
  return doesIdentityRequireRefresh(identity) && identity.expiration.getTime() - Date.now() < expirationMs;
};
var EXPIRATION_MS = 3e5;
var isIdentityExpired = createIsIdentityExpiredFunction(EXPIRATION_MS);
var doesIdentityRequireRefresh = (identity) => identity.expiration !== void 0;
var memoizeIdentityProvider = (provider, isExpired, requiresRefresh) => {
  if (provider === void 0) {
    return void 0;
  }
  const normalizedProvider = typeof provider !== "function" ? async () => Promise.resolve(provider) : provider;
  let resolved;
  let pending;
  let hasResult;
  let isConstant = false;
  const coalesceProvider = async (options) => {
    if (!pending) {
      pending = normalizedProvider(options);
    }
    try {
      resolved = await pending;
      hasResult = true;
      isConstant = false;
    } finally {
      pending = void 0;
    }
    return resolved;
  };
  if (isExpired === void 0) {
    return async (options) => {
      if (!hasResult || options?.forceRefresh) {
        resolved = await coalesceProvider(options);
      }
      return resolved;
    };
  }
  return async (options) => {
    if (!hasResult || options?.forceRefresh) {
      resolved = await coalesceProvider(options);
    }
    if (isConstant) {
      return resolved;
    }
    if (!requiresRefresh(resolved)) {
      isConstant = true;
      return resolved;
    }
    if (isExpired(resolved)) {
      await coalesceProvider(options);
      return resolved;
    }
    return resolved;
  };
};

// node_modules/@aws-sdk/middleware-user-agent/dist-es/configurations.js
var DEFAULT_UA_APP_ID = void 0;
function isValidUserAgentAppId(appId) {
  if (appId === void 0) {
    return true;
  }
  return typeof appId === "string" && appId.length <= 50;
}
function resolveUserAgentConfig(input) {
  const normalizedAppIdProvider = normalizeProvider2(input.userAgentAppId ?? DEFAULT_UA_APP_ID);
  const { customUserAgent } = input;
  return Object.assign(input, {
    customUserAgent: typeof customUserAgent === "string" ? [[customUserAgent]] : customUserAgent,
    userAgentAppId: async () => {
      const appId = await normalizedAppIdProvider();
      if (!isValidUserAgentAppId(appId)) {
        const logger2 = input.logger?.constructor?.name === "NoOpLogger" || !input.logger ? console : input.logger;
        if (typeof appId !== "string") {
          logger2?.warn("userAgentAppId must be a string or undefined.");
        } else if (appId.length > 50) {
          logger2?.warn("The provided userAgentAppId exceeds the maximum length of 50 characters.");
        }
      }
      return appId;
    }
  });
}

// node_modules/@smithy/util-endpoints/dist-es/index.js
init_index_browser();

// node_modules/@aws-sdk/util-endpoints/dist-es/lib/aws/isVirtualHostableS3Bucket.js
var isVirtualHostableS3Bucket = (value, allowSubDomains = false) => {
  if (allowSubDomains) {
    for (const label of value.split(".")) {
      if (!isVirtualHostableS3Bucket(label)) {
        return false;
      }
    }
    return true;
  }
  if (!isValidHostLabel(value)) {
    return false;
  }
  if (value.length < 3 || value.length > 63) {
    return false;
  }
  if (value !== value.toLowerCase()) {
    return false;
  }
  if (isIpAddress(value)) {
    return false;
  }
  return true;
};

// node_modules/@aws-sdk/util-endpoints/dist-es/lib/aws/parseArn.js
var ARN_DELIMITER = ":";
var RESOURCE_DELIMITER = "/";
var parseArn = (value) => {
  const segments = value.split(ARN_DELIMITER);
  if (segments.length < 6)
    return null;
  const [arn, partition2, service, region, accountId, ...resourcePath] = segments;
  if (arn !== "arn" || partition2 === "" || service === "" || resourcePath.join(ARN_DELIMITER) === "")
    return null;
  const resourceId = resourcePath.map((resource) => resource.split(RESOURCE_DELIMITER)).flat();
  return {
    partition: partition2,
    service,
    region,
    accountId,
    resourceId
  };
};

// node_modules/@aws-sdk/util-endpoints/dist-es/lib/aws/partitions.json
var partitions_default = {
  partitions: [{
    id: "aws",
    outputs: {
      dnsSuffix: "amazonaws.com",
      dualStackDnsSuffix: "api.aws",
      implicitGlobalRegion: "us-east-1",
      name: "aws",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^(us|eu|ap|sa|ca|me|af|il|mx)\\-\\w+\\-\\d+$",
    regions: {
      "af-south-1": {
        description: "Africa (Cape Town)"
      },
      "ap-east-1": {
        description: "Asia Pacific (Hong Kong)"
      },
      "ap-east-2": {
        description: "Asia Pacific (Taipei)"
      },
      "ap-northeast-1": {
        description: "Asia Pacific (Tokyo)"
      },
      "ap-northeast-2": {
        description: "Asia Pacific (Seoul)"
      },
      "ap-northeast-3": {
        description: "Asia Pacific (Osaka)"
      },
      "ap-south-1": {
        description: "Asia Pacific (Mumbai)"
      },
      "ap-south-2": {
        description: "Asia Pacific (Hyderabad)"
      },
      "ap-southeast-1": {
        description: "Asia Pacific (Singapore)"
      },
      "ap-southeast-2": {
        description: "Asia Pacific (Sydney)"
      },
      "ap-southeast-3": {
        description: "Asia Pacific (Jakarta)"
      },
      "ap-southeast-4": {
        description: "Asia Pacific (Melbourne)"
      },
      "ap-southeast-5": {
        description: "Asia Pacific (Malaysia)"
      },
      "ap-southeast-6": {
        description: "Asia Pacific (New Zealand)"
      },
      "ap-southeast-7": {
        description: "Asia Pacific (Thailand)"
      },
      "aws-global": {
        description: "aws global region"
      },
      "ca-central-1": {
        description: "Canada (Central)"
      },
      "ca-west-1": {
        description: "Canada West (Calgary)"
      },
      "eu-central-1": {
        description: "Europe (Frankfurt)"
      },
      "eu-central-2": {
        description: "Europe (Zurich)"
      },
      "eu-north-1": {
        description: "Europe (Stockholm)"
      },
      "eu-south-1": {
        description: "Europe (Milan)"
      },
      "eu-south-2": {
        description: "Europe (Spain)"
      },
      "eu-west-1": {
        description: "Europe (Ireland)"
      },
      "eu-west-2": {
        description: "Europe (London)"
      },
      "eu-west-3": {
        description: "Europe (Paris)"
      },
      "il-central-1": {
        description: "Israel (Tel Aviv)"
      },
      "me-central-1": {
        description: "Middle East (UAE)"
      },
      "me-south-1": {
        description: "Middle East (Bahrain)"
      },
      "mx-central-1": {
        description: "Mexico (Central)"
      },
      "sa-east-1": {
        description: "South America (Sao Paulo)"
      },
      "us-east-1": {
        description: "US East (N. Virginia)"
      },
      "us-east-2": {
        description: "US East (Ohio)"
      },
      "us-west-1": {
        description: "US West (N. California)"
      },
      "us-west-2": {
        description: "US West (Oregon)"
      }
    }
  }, {
    id: "aws-cn",
    outputs: {
      dnsSuffix: "amazonaws.com.cn",
      dualStackDnsSuffix: "api.amazonwebservices.com.cn",
      implicitGlobalRegion: "cn-northwest-1",
      name: "aws-cn",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^cn\\-\\w+\\-\\d+$",
    regions: {
      "aws-cn-global": {
        description: "aws-cn global region"
      },
      "cn-north-1": {
        description: "China (Beijing)"
      },
      "cn-northwest-1": {
        description: "China (Ningxia)"
      }
    }
  }, {
    id: "aws-eusc",
    outputs: {
      dnsSuffix: "amazonaws.eu",
      dualStackDnsSuffix: "api.amazonwebservices.eu",
      implicitGlobalRegion: "eusc-de-east-1",
      name: "aws-eusc",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^eusc\\-(de)\\-\\w+\\-\\d+$",
    regions: {
      "eusc-de-east-1": {
        description: "EU (Germany)"
      }
    }
  }, {
    id: "aws-iso",
    outputs: {
      dnsSuffix: "c2s.ic.gov",
      dualStackDnsSuffix: "api.aws.ic.gov",
      implicitGlobalRegion: "us-iso-east-1",
      name: "aws-iso",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^us\\-iso\\-\\w+\\-\\d+$",
    regions: {
      "aws-iso-global": {
        description: "aws-iso global region"
      },
      "us-iso-east-1": {
        description: "US ISO East"
      },
      "us-iso-west-1": {
        description: "US ISO WEST"
      }
    }
  }, {
    id: "aws-iso-b",
    outputs: {
      dnsSuffix: "sc2s.sgov.gov",
      dualStackDnsSuffix: "api.aws.scloud",
      implicitGlobalRegion: "us-isob-east-1",
      name: "aws-iso-b",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^us\\-isob\\-\\w+\\-\\d+$",
    regions: {
      "aws-iso-b-global": {
        description: "aws-iso-b global region"
      },
      "us-isob-east-1": {
        description: "US ISOB East (Ohio)"
      },
      "us-isob-west-1": {
        description: "US ISOB West"
      }
    }
  }, {
    id: "aws-iso-e",
    outputs: {
      dnsSuffix: "cloud.adc-e.uk",
      dualStackDnsSuffix: "api.cloud-aws.adc-e.uk",
      implicitGlobalRegion: "eu-isoe-west-1",
      name: "aws-iso-e",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^eu\\-isoe\\-\\w+\\-\\d+$",
    regions: {
      "aws-iso-e-global": {
        description: "aws-iso-e global region"
      },
      "eu-isoe-west-1": {
        description: "EU ISOE West"
      }
    }
  }, {
    id: "aws-iso-f",
    outputs: {
      dnsSuffix: "csp.hci.ic.gov",
      dualStackDnsSuffix: "api.aws.hci.ic.gov",
      implicitGlobalRegion: "us-isof-south-1",
      name: "aws-iso-f",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^us\\-isof\\-\\w+\\-\\d+$",
    regions: {
      "aws-iso-f-global": {
        description: "aws-iso-f global region"
      },
      "us-isof-east-1": {
        description: "US ISOF EAST"
      },
      "us-isof-south-1": {
        description: "US ISOF SOUTH"
      }
    }
  }, {
    id: "aws-us-gov",
    outputs: {
      dnsSuffix: "amazonaws.com",
      dualStackDnsSuffix: "api.aws",
      implicitGlobalRegion: "us-gov-west-1",
      name: "aws-us-gov",
      supportsDualStack: true,
      supportsFIPS: true
    },
    regionRegex: "^us\\-gov\\-\\w+\\-\\d+$",
    regions: {
      "aws-us-gov-global": {
        description: "aws-us-gov global region"
      },
      "us-gov-east-1": {
        description: "AWS GovCloud (US-East)"
      },
      "us-gov-west-1": {
        description: "AWS GovCloud (US-West)"
      }
    }
  }],
  version: "1.1"
};

// node_modules/@aws-sdk/util-endpoints/dist-es/lib/aws/partition.js
var selectedPartitionsInfo = partitions_default;
var selectedUserAgentPrefix = "";
var partition = (value) => {
  const { partitions } = selectedPartitionsInfo;
  for (const partition2 of partitions) {
    const { regions, outputs } = partition2;
    for (const [region, regionData] of Object.entries(regions)) {
      if (region === value) {
        return {
          ...outputs,
          ...regionData
        };
      }
    }
  }
  for (const partition2 of partitions) {
    const { regionRegex, outputs } = partition2;
    if (new RegExp(regionRegex).test(value)) {
      return {
        ...outputs
      };
    }
  }
  const DEFAULT_PARTITION = partitions.find((partition2) => partition2.id === "aws");
  if (!DEFAULT_PARTITION) {
    throw new Error("Provided region was not found in the partition array or regex, and default partition with id 'aws' doesn't exist.");
  }
  return {
    ...DEFAULT_PARTITION.outputs
  };
};
var getUserAgentPrefix = () => selectedUserAgentPrefix;

// node_modules/@aws-sdk/util-endpoints/dist-es/aws.js
var awsEndpointFunctions = {
  isVirtualHostableS3Bucket,
  parseArn,
  partition
};
customEndpointFunctions.aws = awsEndpointFunctions;

// node_modules/@aws-sdk/core/dist-es/submodules/client/setCredentialFeature.js
function setCredentialFeature(credentials, feature, value) {
  if (!credentials.$source) {
    credentials.$source = {};
  }
  credentials.$source[feature] = value;
  return credentials;
}

// node_modules/@aws-sdk/core/dist-es/submodules/client/setFeature.js
function setFeature2(context, feature, value) {
  if (!context.__aws_sdk_context) {
    context.__aws_sdk_context = {
      features: {}
    };
  } else if (!context.__aws_sdk_context.features) {
    context.__aws_sdk_context.features = {};
  }
  context.__aws_sdk_context.features[feature] = value;
}

// node_modules/@aws-sdk/core/dist-es/submodules/httpAuthSchemes/utils/getDateHeader.js
var getDateHeader = (response) => HttpResponse.isInstance(response) ? response.headers?.date ?? response.headers?.Date : void 0;

// node_modules/@aws-sdk/core/dist-es/submodules/httpAuthSchemes/utils/getSkewCorrectedDate.js
var getSkewCorrectedDate = (systemClockOffset) => new Date(Date.now() + systemClockOffset);

// node_modules/@aws-sdk/core/dist-es/submodules/httpAuthSchemes/utils/isClockSkewed.js
var isClockSkewed = (clockTime, systemClockOffset) => Math.abs(getSkewCorrectedDate(systemClockOffset).getTime() - clockTime) >= 3e5;

// node_modules/@aws-sdk/core/dist-es/submodules/httpAuthSchemes/utils/getUpdatedSystemClockOffset.js
var getUpdatedSystemClockOffset = (clockTime, currentSystemClockOffset) => {
  const clockTimeInMs = Date.parse(clockTime);
  if (isClockSkewed(clockTimeInMs, currentSystemClockOffset)) {
    return clockTimeInMs - Date.now();
  }
  return currentSystemClockOffset;
};

// node_modules/@aws-sdk/core/dist-es/submodules/httpAuthSchemes/aws_sdk/AwsSdkSigV4Signer.js
var throwSigningPropertyError = (name, property) => {
  if (!property) {
    throw new Error(`Property \`${name}\` is not resolved for AWS SDK SigV4Auth`);
  }
  return property;
};
var validateSigningProperties = async (signingProperties) => {
  const context = throwSigningPropertyError("context", signingProperties.context);
  const config = throwSigningPropertyError("config", signingProperties.config);
  const authScheme = context.endpointV2?.properties?.authSchemes?.[0];
  const signerFunction = throwSigningPropertyError("signer", config.signer);
  const signer = await signerFunction(authScheme);
  const signingRegion = signingProperties?.signingRegion;
  const signingRegionSet = signingProperties?.signingRegionSet;
  const signingName = signingProperties?.signingName;
  return {
    config,
    signer,
    signingRegion,
    signingRegionSet,
    signingName
  };
};
var AwsSdkSigV4Signer = class {
  async sign(httpRequest, identity, signingProperties) {
    if (!HttpRequest.isInstance(httpRequest)) {
      throw new Error("The request is not an instance of `HttpRequest` and cannot be signed");
    }
    const validatedProps = await validateSigningProperties(signingProperties);
    const { config, signer } = validatedProps;
    let { signingRegion, signingName } = validatedProps;
    const handlerExecutionContext = signingProperties.context;
    if (handlerExecutionContext?.authSchemes?.length ?? 0 > 1) {
      const [first, second] = handlerExecutionContext.authSchemes;
      if (first?.name === "sigv4a" && second?.name === "sigv4") {
        signingRegion = second?.signingRegion ?? signingRegion;
        signingName = second?.signingName ?? signingName;
      }
    }
    const signedRequest = await signer.sign(httpRequest, {
      signingDate: getSkewCorrectedDate(config.systemClockOffset),
      signingRegion,
      signingService: signingName
    });
    return signedRequest;
  }
  errorHandler(signingProperties) {
    return (error) => {
      const serverTime = error.ServerTime ?? getDateHeader(error.$response);
      if (serverTime) {
        const config = throwSigningPropertyError("config", signingProperties.config);
        const initialSystemClockOffset = config.systemClockOffset;
        config.systemClockOffset = getUpdatedSystemClockOffset(serverTime, config.systemClockOffset);
        const clockSkewCorrected = config.systemClockOffset !== initialSystemClockOffset;
        if (clockSkewCorrected && error.$metadata) {
          error.$metadata.clockSkewCorrected = true;
        }
      }
      throw error;
    };
  }
  successHandler(httpResponse, signingProperties) {
    const dateHeader = getDateHeader(httpResponse);
    if (dateHeader) {
      const config = throwSigningPropertyError("config", signingProperties.config);
      config.systemClockOffset = getUpdatedSystemClockOffset(dateHeader, config.systemClockOffset);
    }
  }
};

// node_modules/@smithy/core/dist-es/submodules/config/property-provider/memoize.js
var memoize = (provider, isExpired, requiresRefresh) => {
  let resolved;
  let pending;
  let hasResult;
  let isConstant = false;
  const coalesceProvider = async () => {
    if (!pending) {
      pending = provider();
    }
    try {
      resolved = await pending;
      hasResult = true;
      isConstant = false;
    } finally {
      pending = void 0;
    }
    return resolved;
  };
  if (isExpired === void 0) {
    return async (options) => {
      if (!hasResult || options?.forceRefresh) {
        resolved = await coalesceProvider();
      }
      return resolved;
    };
  }
  return async (options) => {
    if (!hasResult || options?.forceRefresh) {
      resolved = await coalesceProvider();
    }
    if (isConstant) {
      return resolved;
    }
    if (requiresRefresh && !requiresRefresh(resolved)) {
      isConstant = true;
      return resolved;
    }
    if (isExpired(resolved)) {
      await coalesceProvider();
      return resolved;
    }
    return resolved;
  };
};

// node_modules/@smithy/core/dist-es/submodules/client/middleware-stack/MiddlewareStack.js
var getAllAliases = (name, aliases) => {
  const _aliases = [];
  if (name) {
    _aliases.push(name);
  }
  if (aliases) {
    for (const alias of aliases) {
      _aliases.push(alias);
    }
  }
  return _aliases;
};
var getMiddlewareNameWithAliases = (name, aliases) => {
  return `${name || "anonymous"}${aliases && aliases.length > 0 ? ` (a.k.a. ${aliases.join(",")})` : ""}`;
};
var constructStack = () => {
  let absoluteEntries = [];
  let relativeEntries = [];
  let identifyOnResolve = false;
  const entriesNameSet = /* @__PURE__ */ new Set();
  const sort = (entries) => entries.sort((a2, b2) => stepWeights[b2.step] - stepWeights[a2.step] || priorityWeights[b2.priority || "normal"] - priorityWeights[a2.priority || "normal"]);
  const removeByName = (toRemove) => {
    let isRemoved = false;
    const filterCb = (entry) => {
      const aliases = getAllAliases(entry.name, entry.aliases);
      if (aliases.includes(toRemove)) {
        isRemoved = true;
        for (const alias of aliases) {
          entriesNameSet.delete(alias);
        }
        return false;
      }
      return true;
    };
    absoluteEntries = absoluteEntries.filter(filterCb);
    relativeEntries = relativeEntries.filter(filterCb);
    return isRemoved;
  };
  const removeByReference = (toRemove) => {
    let isRemoved = false;
    const filterCb = (entry) => {
      if (entry.middleware === toRemove) {
        isRemoved = true;
        for (const alias of getAllAliases(entry.name, entry.aliases)) {
          entriesNameSet.delete(alias);
        }
        return false;
      }
      return true;
    };
    absoluteEntries = absoluteEntries.filter(filterCb);
    relativeEntries = relativeEntries.filter(filterCb);
    return isRemoved;
  };
  const cloneTo = (toStack) => {
    absoluteEntries.forEach((entry) => {
      toStack.add(entry.middleware, { ...entry });
    });
    relativeEntries.forEach((entry) => {
      toStack.addRelativeTo(entry.middleware, { ...entry });
    });
    toStack.identifyOnResolve?.(stack.identifyOnResolve());
    return toStack;
  };
  const expandRelativeMiddlewareList = (from) => {
    const expandedMiddlewareList = [];
    from.before.forEach((entry) => {
      if (entry.before.length === 0 && entry.after.length === 0) {
        expandedMiddlewareList.push(entry);
      } else {
        expandedMiddlewareList.push(...expandRelativeMiddlewareList(entry));
      }
    });
    expandedMiddlewareList.push(from);
    from.after.reverse().forEach((entry) => {
      if (entry.before.length === 0 && entry.after.length === 0) {
        expandedMiddlewareList.push(entry);
      } else {
        expandedMiddlewareList.push(...expandRelativeMiddlewareList(entry));
      }
    });
    return expandedMiddlewareList;
  };
  const getMiddlewareList = (debug = false) => {
    const normalizedAbsoluteEntries = [];
    const normalizedRelativeEntries = [];
    const normalizedEntriesNameMap = {};
    absoluteEntries.forEach((entry) => {
      const normalizedEntry = {
        ...entry,
        before: [],
        after: []
      };
      for (const alias of getAllAliases(normalizedEntry.name, normalizedEntry.aliases)) {
        normalizedEntriesNameMap[alias] = normalizedEntry;
      }
      normalizedAbsoluteEntries.push(normalizedEntry);
    });
    relativeEntries.forEach((entry) => {
      const normalizedEntry = {
        ...entry,
        before: [],
        after: []
      };
      for (const alias of getAllAliases(normalizedEntry.name, normalizedEntry.aliases)) {
        normalizedEntriesNameMap[alias] = normalizedEntry;
      }
      normalizedRelativeEntries.push(normalizedEntry);
    });
    normalizedRelativeEntries.forEach((entry) => {
      if (entry.toMiddleware) {
        const toMiddleware = normalizedEntriesNameMap[entry.toMiddleware];
        if (toMiddleware === void 0) {
          if (debug) {
            return;
          }
          throw new Error(`${entry.toMiddleware} is not found when adding ${getMiddlewareNameWithAliases(entry.name, entry.aliases)} middleware ${entry.relation} ${entry.toMiddleware}`);
        }
        if (entry.relation === "after") {
          toMiddleware.after.push(entry);
        }
        if (entry.relation === "before") {
          toMiddleware.before.push(entry);
        }
      }
    });
    const mainChain = sort(normalizedAbsoluteEntries).map(expandRelativeMiddlewareList).reduce((wholeList, expandedMiddlewareList) => {
      wholeList.push(...expandedMiddlewareList);
      return wholeList;
    }, []);
    return mainChain;
  };
  const stack = {
    add: (middleware, options = {}) => {
      const { name, override, aliases: _aliases } = options;
      const entry = {
        step: "initialize",
        priority: "normal",
        middleware,
        ...options
      };
      const aliases = getAllAliases(name, _aliases);
      if (aliases.length > 0) {
        if (aliases.some((alias) => entriesNameSet.has(alias))) {
          if (!override)
            throw new Error(`Duplicate middleware name '${getMiddlewareNameWithAliases(name, _aliases)}'`);
          for (const alias of aliases) {
            const toOverrideIndex = absoluteEntries.findIndex((entry2) => entry2.name === alias || entry2.aliases?.some((a2) => a2 === alias));
            if (toOverrideIndex === -1) {
              continue;
            }
            const toOverride = absoluteEntries[toOverrideIndex];
            if (toOverride.step !== entry.step || entry.priority !== toOverride.priority) {
              throw new Error(`"${getMiddlewareNameWithAliases(toOverride.name, toOverride.aliases)}" middleware with ${toOverride.priority} priority in ${toOverride.step} step cannot be overridden by "${getMiddlewareNameWithAliases(name, _aliases)}" middleware with ${entry.priority} priority in ${entry.step} step.`);
            }
            absoluteEntries.splice(toOverrideIndex, 1);
          }
        }
        for (const alias of aliases) {
          entriesNameSet.add(alias);
        }
      }
      absoluteEntries.push(entry);
    },
    addRelativeTo: (middleware, options) => {
      const { name, override, aliases: _aliases } = options;
      const entry = {
        middleware,
        ...options
      };
      const aliases = getAllAliases(name, _aliases);
      if (aliases.length > 0) {
        if (aliases.some((alias) => entriesNameSet.has(alias))) {
          if (!override)
            throw new Error(`Duplicate middleware name '${getMiddlewareNameWithAliases(name, _aliases)}'`);
          for (const alias of aliases) {
            const toOverrideIndex = relativeEntries.findIndex((entry2) => entry2.name === alias || entry2.aliases?.some((a2) => a2 === alias));
            if (toOverrideIndex === -1) {
              continue;
            }
            const toOverride = relativeEntries[toOverrideIndex];
            if (toOverride.toMiddleware !== entry.toMiddleware || toOverride.relation !== entry.relation) {
              throw new Error(`"${getMiddlewareNameWithAliases(toOverride.name, toOverride.aliases)}" middleware ${toOverride.relation} "${toOverride.toMiddleware}" middleware cannot be overridden by "${getMiddlewareNameWithAliases(name, _aliases)}" middleware ${entry.relation} "${entry.toMiddleware}" middleware.`);
            }
            relativeEntries.splice(toOverrideIndex, 1);
          }
        }
        for (const alias of aliases) {
          entriesNameSet.add(alias);
        }
      }
      relativeEntries.push(entry);
    },
    clone: () => cloneTo(constructStack()),
    use: (plugin) => {
      plugin.applyToStack(stack);
    },
    remove: (toRemove) => {
      if (typeof toRemove === "string")
        return removeByName(toRemove);
      else
        return removeByReference(toRemove);
    },
    removeByTag: (toRemove) => {
      let isRemoved = false;
      const filterCb = (entry) => {
        const { tags, name, aliases: _aliases } = entry;
        if (tags && tags.includes(toRemove)) {
          const aliases = getAllAliases(name, _aliases);
          for (const alias of aliases) {
            entriesNameSet.delete(alias);
          }
          isRemoved = true;
          return false;
        }
        return true;
      };
      absoluteEntries = absoluteEntries.filter(filterCb);
      relativeEntries = relativeEntries.filter(filterCb);
      return isRemoved;
    },
    concat: (from) => {
      const cloned = cloneTo(constructStack());
      cloned.use(from);
      cloned.identifyOnResolve(identifyOnResolve || cloned.identifyOnResolve() || (from.identifyOnResolve?.() ?? false));
      return cloned;
    },
    applyToStack: cloneTo,
    identify: () => {
      return getMiddlewareList(true).map((mw) => {
        const step = mw.step ?? mw.relation + " " + mw.toMiddleware;
        return getMiddlewareNameWithAliases(mw.name, mw.aliases) + " - " + step;
      });
    },
    identifyOnResolve(toggle) {
      if (typeof toggle === "boolean")
        identifyOnResolve = toggle;
      return identifyOnResolve;
    },
    resolve: (handler, context) => {
      for (const middleware of getMiddlewareList().map((entry) => entry.middleware).reverse()) {
        handler = middleware(handler, context);
      }
      if (identifyOnResolve) {
        console.log(stack.identify());
      }
      return handler;
    }
  };
  return stack;
};
var stepWeights = {
  initialize: 5,
  serialize: 4,
  build: 3,
  finalizeRequest: 2,
  deserialize: 1
};
var priorityWeights = {
  high: 3,
  normal: 2,
  low: 1
};

// node_modules/@smithy/core/dist-es/submodules/client/index.js
init_transport();
init_transport();

// node_modules/@smithy/core/dist-es/submodules/client/invalid-dependency/invalidProvider.js
var invalidProvider = (message) => () => Promise.reject(message);

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/client.js
var Client = class {
  config;
  middlewareStack = constructStack();
  initConfig;
  handlers;
  constructor(config) {
    this.config = config;
    const { protocol, protocolSettings } = config;
    if (protocolSettings) {
      if (typeof protocol === "function") {
        config.protocol = new protocol(protocolSettings);
      }
    }
  }
  send(command, optionsOrCb, cb) {
    const options = typeof optionsOrCb !== "function" ? optionsOrCb : void 0;
    const callback = typeof optionsOrCb === "function" ? optionsOrCb : cb;
    const useHandlerCache = options === void 0 && this.config.cacheMiddleware === true;
    let handler;
    if (useHandlerCache) {
      if (!this.handlers) {
        this.handlers = /* @__PURE__ */ new WeakMap();
      }
      const handlers = this.handlers;
      if (handlers.has(command.constructor)) {
        handler = handlers.get(command.constructor);
      } else {
        handler = command.resolveMiddleware(this.middlewareStack, this.config, options);
        handlers.set(command.constructor, handler);
      }
    } else {
      delete this.handlers;
      handler = command.resolveMiddleware(this.middlewareStack, this.config, options);
    }
    if (callback) {
      handler(command).then((result) => callback(null, result.output), (err) => callback(err)).catch(() => {
      });
    } else {
      return handler(command).then((result) => result.output);
    }
  }
  destroy() {
    this.config?.requestHandler?.destroy?.();
    delete this.handlers;
  }
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/command.js
init_dist_es();

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/schemaLogFilter.js
var SENSITIVE_STRING = "***SensitiveInformation***";
function schemaLogFilter(schema, data) {
  if (data == null) {
    return data;
  }
  const ns = NormalizedSchema.of(schema);
  if (ns.getMergedTraits().sensitive) {
    return SENSITIVE_STRING;
  }
  if (ns.isListSchema()) {
    const isSensitive = !!ns.getValueSchema().getMergedTraits().sensitive;
    if (isSensitive) {
      return SENSITIVE_STRING;
    }
  } else if (ns.isMapSchema()) {
    const isSensitive = !!ns.getKeySchema().getMergedTraits().sensitive || !!ns.getValueSchema().getMergedTraits().sensitive;
    if (isSensitive) {
      return SENSITIVE_STRING;
    }
  } else if (ns.isStructSchema() && typeof data === "object") {
    const object = data;
    const newObject = {};
    for (const [member2, memberNs] of ns.structIterator()) {
      if (object[member2] != null) {
        newObject[member2] = schemaLogFilter(memberNs, object[member2]);
      }
    }
    return newObject;
  }
  return data;
}

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/command.js
var Command = class {
  middlewareStack = constructStack();
  schema;
  static classBuilder() {
    return new ClassBuilder();
  }
  resolveMiddlewareWithContext(clientStack, configuration, options, { middlewareFn, clientName, commandName, inputFilterSensitiveLog, outputFilterSensitiveLog, smithyContext, additionalContext, CommandCtor }) {
    for (const mw of middlewareFn.bind(this)(CommandCtor, clientStack, configuration, options)) {
      this.middlewareStack.use(mw);
    }
    const stack = clientStack.concat(this.middlewareStack);
    const { logger: logger2 } = configuration;
    const handlerExecutionContext = {
      logger: logger2,
      clientName,
      commandName,
      inputFilterSensitiveLog,
      outputFilterSensitiveLog,
      [SMITHY_CONTEXT_KEY]: {
        commandInstance: this,
        ...smithyContext
      },
      ...additionalContext
    };
    const { requestHandler } = configuration;
    let requestOptions = options ?? {};
    if (smithyContext.eventStream) {
      requestOptions = {
        isEventStream: true,
        ...requestOptions
      };
    }
    return stack.resolve((request) => requestHandler.handle(request.request, requestOptions), handlerExecutionContext);
  }
};
var ClassBuilder = class {
  _init = () => {
  };
  _ep = {};
  _middlewareFn = () => [];
  _commandName = "";
  _clientName = "";
  _additionalContext = {};
  _smithyContext = {};
  _inputFilterSensitiveLog = void 0;
  _outputFilterSensitiveLog = void 0;
  _serializer = null;
  _deserializer = null;
  _operationSchema;
  init(cb) {
    this._init = cb;
  }
  ep(endpointParameterInstructions) {
    this._ep = endpointParameterInstructions;
    return this;
  }
  m(middlewareSupplier) {
    this._middlewareFn = middlewareSupplier;
    return this;
  }
  s(service, operation2, smithyContext = {}) {
    this._smithyContext = {
      service,
      operation: operation2,
      ...smithyContext
    };
    return this;
  }
  c(additionalContext = {}) {
    this._additionalContext = additionalContext;
    return this;
  }
  n(clientName, commandName) {
    this._clientName = clientName;
    this._commandName = commandName;
    return this;
  }
  f(inputFilter = (_) => _, outputFilter = (_) => _) {
    this._inputFilterSensitiveLog = inputFilter;
    this._outputFilterSensitiveLog = outputFilter;
    return this;
  }
  ser(serializer) {
    this._serializer = serializer;
    return this;
  }
  de(deserializer) {
    this._deserializer = deserializer;
    return this;
  }
  sc(operation2) {
    this._operationSchema = operation2;
    this._smithyContext.operationSchema = operation2;
    return this;
  }
  build() {
    const closure = this;
    let CommandRef;
    return CommandRef = class extends Command {
      input;
      static getEndpointParameterInstructions() {
        return closure._ep;
      }
      constructor(...[input]) {
        super();
        this.input = input ?? {};
        closure._init(this);
        this.schema = closure._operationSchema;
      }
      resolveMiddleware(stack, configuration, options) {
        const op = closure._operationSchema;
        const input = op?.[4] ?? op?.input;
        const output = op?.[5] ?? op?.output;
        return this.resolveMiddlewareWithContext(stack, configuration, options, {
          CommandCtor: CommandRef,
          middlewareFn: closure._middlewareFn,
          clientName: closure._clientName,
          commandName: closure._commandName,
          inputFilterSensitiveLog: closure._inputFilterSensitiveLog ?? (op ? schemaLogFilter.bind(null, input) : (_) => _),
          outputFilterSensitiveLog: closure._outputFilterSensitiveLog ?? (op ? schemaLogFilter.bind(null, output) : (_) => _),
          smithyContext: closure._smithyContext,
          additionalContext: closure._additionalContext
        });
      }
      serialize = closure._serializer;
      deserialize = closure._deserializer;
    };
  }
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/create-aggregated-client.js
var createAggregatedClient = (commands2, Client2, options) => {
  for (const [command, CommandCtor] of Object.entries(commands2)) {
    const methodImpl = async function(args, optionsOrCb, cb) {
      const command2 = new CommandCtor(args);
      if (typeof optionsOrCb === "function") {
        this.send(command2, optionsOrCb);
      } else if (typeof cb === "function") {
        if (typeof optionsOrCb !== "object")
          throw new Error(`Expected http options but got ${typeof optionsOrCb}`);
        this.send(command2, optionsOrCb || {}, cb);
      } else {
        return this.send(command2, optionsOrCb);
      }
    };
    const methodName = (command[0].toLowerCase() + command.slice(1)).replace(/Command$/, "");
    Client2.prototype[methodName] = methodImpl;
  }
  const { paginators = {}, waiters = {} } = options ?? {};
  for (const [paginatorName, paginatorFn] of Object.entries(paginators)) {
    if (Client2.prototype[paginatorName] === void 0) {
      Client2.prototype[paginatorName] = function(commandInput = {}, paginationConfiguration, ...rest) {
        return paginatorFn({
          ...paginationConfiguration,
          client: this
        }, commandInput, ...rest);
      };
    }
  }
  for (const [waiterName, waiterFn] of Object.entries(waiters)) {
    if (Client2.prototype[waiterName] === void 0) {
      Client2.prototype[waiterName] = async function(commandInput = {}, waiterConfiguration, ...rest) {
        let config = waiterConfiguration;
        if (typeof waiterConfiguration === "number") {
          config = {
            maxWaitTime: waiterConfiguration
          };
        }
        return waiterFn({
          ...config,
          client: this
        }, commandInput, ...rest);
      };
    }
  }
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/exceptions.js
var ServiceException = class _ServiceException extends Error {
  $fault;
  $response;
  $retryable;
  $metadata;
  constructor(options) {
    super(options.message);
    Object.setPrototypeOf(this, Object.getPrototypeOf(this).constructor.prototype);
    this.name = options.name;
    this.$fault = options.$fault;
    this.$metadata = options.$metadata;
  }
  static isInstance(value) {
    if (!value)
      return false;
    const candidate = value;
    return _ServiceException.prototype.isPrototypeOf(candidate) || Boolean(candidate.$fault) && Boolean(candidate.$metadata) && (candidate.$fault === "client" || candidate.$fault === "server");
  }
  static [Symbol.hasInstance](instance) {
    if (!instance)
      return false;
    const candidate = instance;
    if (this === _ServiceException) {
      return _ServiceException.isInstance(instance);
    }
    if (_ServiceException.isInstance(instance)) {
      if (candidate.name && this.name) {
        return this.prototype.isPrototypeOf(instance) || candidate.name === this.name;
      }
      return this.prototype.isPrototypeOf(instance);
    }
    return false;
  }
};
var decorateServiceException = (exception, additions = {}) => {
  Object.entries(additions).filter(([, v2]) => v2 !== void 0).forEach(([k2, v2]) => {
    if (exception[k2] == void 0 || exception[k2] === "") {
      exception[k2] = v2;
    }
  });
  const message = exception.message || exception.Message || "UnknownError";
  exception.message = message;
  delete exception.Message;
  return exception;
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/defaults-mode.js
var loadConfigsForDefaultMode = (mode) => {
  switch (mode) {
    case "standard":
      return {
        retryMode: "standard",
        connectionTimeout: 3100
      };
    case "in-region":
      return {
        retryMode: "standard",
        connectionTimeout: 1100
      };
    case "cross-region":
      return {
        retryMode: "standard",
        connectionTimeout: 3100
      };
    case "mobile":
      return {
        retryMode: "standard",
        connectionTimeout: 3e4
      };
    default:
      return {};
  }
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/extensions/checksum.js
init_dist_es();
var knownAlgorithms = Object.values(AlgorithmId);
var getChecksumConfiguration = (runtimeConfig) => {
  const checksumAlgorithms = [];
  for (const id in AlgorithmId) {
    const algorithmId = AlgorithmId[id];
    if (runtimeConfig[algorithmId] === void 0) {
      continue;
    }
    checksumAlgorithms.push({
      algorithmId: () => algorithmId,
      checksumConstructor: () => runtimeConfig[algorithmId]
    });
  }
  for (const [id, ChecksumCtor] of Object.entries(runtimeConfig.checksumAlgorithms ?? {})) {
    checksumAlgorithms.push({
      algorithmId: () => id,
      checksumConstructor: () => ChecksumCtor
    });
  }
  return {
    addChecksumAlgorithm(algo) {
      runtimeConfig.checksumAlgorithms = runtimeConfig.checksumAlgorithms ?? {};
      const id = algo.algorithmId();
      const ctor = algo.checksumConstructor();
      if (knownAlgorithms.includes(id)) {
        runtimeConfig.checksumAlgorithms[id.toUpperCase()] = ctor;
      } else {
        runtimeConfig.checksumAlgorithms[id] = ctor;
      }
      checksumAlgorithms.push(algo);
    },
    checksumAlgorithms() {
      return checksumAlgorithms;
    }
  };
};
var resolveChecksumRuntimeConfig = (clientConfig) => {
  const runtimeConfig = {};
  clientConfig.checksumAlgorithms().forEach((checksumAlgorithm) => {
    const id = checksumAlgorithm.algorithmId();
    if (knownAlgorithms.includes(id)) {
      runtimeConfig[id] = checksumAlgorithm.checksumConstructor();
    }
  });
  return runtimeConfig;
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/extensions/retry.js
var getRetryConfiguration = (runtimeConfig) => {
  return {
    setRetryStrategy(retryStrategy) {
      runtimeConfig.retryStrategy = retryStrategy;
    },
    retryStrategy() {
      return runtimeConfig.retryStrategy;
    }
  };
};
var resolveRetryRuntimeConfig = (retryStrategyConfiguration) => {
  const runtimeConfig = {};
  runtimeConfig.retryStrategy = retryStrategyConfiguration.retryStrategy();
  return runtimeConfig;
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/extensions/defaultExtensionConfiguration.js
var getDefaultExtensionConfiguration = (runtimeConfig) => {
  return Object.assign(getChecksumConfiguration(runtimeConfig), getRetryConfiguration(runtimeConfig));
};
var resolveDefaultRuntimeConfig2 = (config) => {
  return Object.assign(resolveChecksumRuntimeConfig(config), resolveRetryRuntimeConfig(config));
};

// node_modules/@smithy/core/dist-es/submodules/client/smithy-client/NoOpLogger.js
var NoOpLogger = class {
  trace() {
  }
  debug() {
  }
  info() {
  }
  warn() {
  }
  error() {
  }
};

// node_modules/@smithy/core/dist-es/submodules/config/config-resolver/regionConfig/checkRegion.js
init_transport();
var validRegions = /* @__PURE__ */ new Set();
var checkRegion = (region, check = isValidHostLabel) => {
  if (!validRegions.has(region) && !check(region)) {
    if (region === "*") {
      console.warn(`@smithy/config-resolver WARN - Please use the caller region instead of "*". See "sigv4a" in https://github.com/aws/aws-sdk-js-v3/blob/main/supplemental-docs/CLIENTS.md.`);
    } else {
      throw new Error(`Region not accepted: region="${region}" is not a valid hostname component.`);
    }
  } else {
    validRegions.add(region);
  }
};

// node_modules/@smithy/core/dist-es/submodules/config/config-resolver/regionConfig/isFipsRegion.js
var isFipsRegion = (region) => typeof region === "string" && (region.startsWith("fips-") || region.endsWith("-fips"));

// node_modules/@smithy/core/dist-es/submodules/config/config-resolver/regionConfig/getRealRegion.js
var getRealRegion = (region) => isFipsRegion(region) ? ["fips-aws-global", "aws-fips"].includes(region) ? "us-east-1" : region.replace(/fips-(dkr-|prod-)?|-fips/, "") : region;

// node_modules/@smithy/core/dist-es/submodules/config/config-resolver/regionConfig/resolveRegionConfig.js
var resolveRegionConfig = (input) => {
  const { region, useFipsEndpoint } = input;
  if (!region) {
    throw new Error("Region is missing");
  }
  return Object.assign(input, {
    region: async () => {
      const providedRegion = typeof region === "function" ? await region() : region;
      const realRegion = getRealRegion(providedRegion);
      checkRegion(realRegion);
      return realRegion;
    },
    useFipsEndpoint: async () => {
      const providedRegion = typeof region === "string" ? region : await region();
      if (isFipsRegion(providedRegion)) {
        return true;
      }
      return typeof useFipsEndpoint !== "function" ? Promise.resolve(!!useFipsEndpoint) : useFipsEndpoint();
    }
  });
};

// node_modules/@smithy/core/dist-es/submodules/config/defaults-mode/constants.js
var DEFAULTS_MODE_OPTIONS = ["in-region", "cross-region", "mobile", "standard", "legacy"];

// node_modules/@smithy/core/dist-es/submodules/config/defaults-mode/resolveDefaultsModeConfig.browser.js
var resolveDefaultsModeConfig = ({ defaultsMode } = {}) => memoize(async () => {
  const mode = typeof defaultsMode === "function" ? await defaultsMode() : defaultsMode;
  switch (mode?.toLowerCase()) {
    case "auto":
      return Promise.resolve(useMobileConfiguration() ? "mobile" : "standard");
    case "mobile":
    case "in-region":
    case "cross-region":
    case "standard":
    case "legacy":
      return Promise.resolve(mode?.toLocaleLowerCase());
    case void 0:
      return Promise.resolve("legacy");
    default:
      throw new Error(`Invalid parameter for "defaultsMode", expect ${DEFAULTS_MODE_OPTIONS.join(", ")}, got ${mode}`);
  }
});
var useMobileConfiguration = () => {
  const navigator = window?.navigator;
  if (navigator?.connection) {
    const { effectiveType, rtt, downlink } = navigator?.connection;
    const slow = typeof effectiveType === "string" && effectiveType !== "4g" || Number(rtt) > 100 || Number(downlink) < 10;
    if (slow) {
      return true;
    }
  }
  return navigator?.userAgentData?.mobile || typeof navigator?.maxTouchPoints === "number" && navigator?.maxTouchPoints > 1;
};

// node_modules/@smithy/core/dist-es/submodules/config/index.browser.js
var DEFAULT_USE_DUALSTACK_ENDPOINT = false;
var DEFAULT_USE_FIPS_ENDPOINT = false;

// node_modules/@smithy/signature-v4/dist-es/SignatureV4.js
init_index_browser2();

// node_modules/@smithy/signature-v4/dist-es/HeaderFormatter.js
init_index_browser2();
var HeaderFormatter = class {
  format(headers) {
    const chunks = [];
    for (const headerName of Object.keys(headers)) {
      const bytes = fromUtf8(headerName);
      chunks.push(Uint8Array.from([bytes.byteLength]), bytes, this.formatHeaderValue(headers[headerName]));
    }
    const out = new Uint8Array(chunks.reduce((carry, bytes) => carry + bytes.byteLength, 0));
    let position = 0;
    for (const chunk of chunks) {
      out.set(chunk, position);
      position += chunk.byteLength;
    }
    return out;
  }
  formatHeaderValue(header) {
    switch (header.type) {
      case "boolean":
        return Uint8Array.from([header.value ? 0 : 1]);
      case "byte":
        return Uint8Array.from([2, header.value]);
      case "short":
        const shortView = new DataView(new ArrayBuffer(3));
        shortView.setUint8(0, 3);
        shortView.setInt16(1, header.value, false);
        return new Uint8Array(shortView.buffer);
      case "integer":
        const intView = new DataView(new ArrayBuffer(5));
        intView.setUint8(0, 4);
        intView.setInt32(1, header.value, false);
        return new Uint8Array(intView.buffer);
      case "long":
        const longBytes = new Uint8Array(9);
        longBytes[0] = 5;
        longBytes.set(header.value.bytes, 1);
        return longBytes;
      case "binary":
        const binView = new DataView(new ArrayBuffer(3 + header.value.byteLength));
        binView.setUint8(0, 6);
        binView.setUint16(1, header.value.byteLength, false);
        const binBytes = new Uint8Array(binView.buffer);
        binBytes.set(header.value, 3);
        return binBytes;
      case "string":
        const utf8Bytes = fromUtf8(header.value);
        const strView = new DataView(new ArrayBuffer(3 + utf8Bytes.byteLength));
        strView.setUint8(0, 7);
        strView.setUint16(1, utf8Bytes.byteLength, false);
        const strBytes = new Uint8Array(strView.buffer);
        strBytes.set(utf8Bytes, 3);
        return strBytes;
      case "timestamp":
        const tsBytes = new Uint8Array(9);
        tsBytes[0] = 8;
        tsBytes.set(Int642.fromNumber(header.value.valueOf()).bytes, 1);
        return tsBytes;
      case "uuid":
        if (!UUID_PATTERN2.test(header.value)) {
          throw new Error(`Invalid UUID received: ${header.value}`);
        }
        const uuidBytes = new Uint8Array(17);
        uuidBytes[0] = 9;
        uuidBytes.set(fromHex(header.value.replace(/\-/g, "")), 1);
        return uuidBytes;
    }
  }
};
var HEADER_VALUE_TYPE2;
(function(HEADER_VALUE_TYPE3) {
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["boolTrue"] = 0] = "boolTrue";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["boolFalse"] = 1] = "boolFalse";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["byte"] = 2] = "byte";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["short"] = 3] = "short";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["integer"] = 4] = "integer";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["long"] = 5] = "long";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["byteArray"] = 6] = "byteArray";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["string"] = 7] = "string";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["timestamp"] = 8] = "timestamp";
  HEADER_VALUE_TYPE3[HEADER_VALUE_TYPE3["uuid"] = 9] = "uuid";
})(HEADER_VALUE_TYPE2 || (HEADER_VALUE_TYPE2 = {}));
var UUID_PATTERN2 = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
var Int642 = class _Int64 {
  bytes;
  constructor(bytes) {
    this.bytes = bytes;
    if (bytes.byteLength !== 8) {
      throw new Error("Int64 buffers must be exactly 8 bytes");
    }
  }
  static fromNumber(number) {
    if (number > 9223372036854776e3 || number < -9223372036854776e3) {
      throw new Error(`${number} is too large (or, if negative, too small) to represent as an Int64`);
    }
    const bytes = new Uint8Array(8);
    for (let i2 = 7, remaining = Math.abs(Math.round(number)); i2 > -1 && remaining > 0; i2--, remaining /= 256) {
      bytes[i2] = remaining;
    }
    if (number < 0) {
      negate2(bytes);
    }
    return new _Int64(bytes);
  }
  valueOf() {
    const bytes = this.bytes.slice(0);
    const negative = bytes[0] & 128;
    if (negative) {
      negate2(bytes);
    }
    return parseInt(toHex(bytes), 16) * (negative ? -1 : 1);
  }
  toString() {
    return String(this.valueOf());
  }
};
function negate2(bytes) {
  for (let i2 = 0; i2 < 8; i2++) {
    bytes[i2] ^= 255;
  }
  for (let i2 = 7; i2 > -1; i2--) {
    bytes[i2]++;
    if (bytes[i2] !== 0)
      break;
  }
}

// node_modules/@smithy/signature-v4/dist-es/SignatureV4Base.js
init_index_browser2();

// node_modules/@smithy/signature-v4/dist-es/constants.js
var ALGORITHM_QUERY_PARAM = "X-Amz-Algorithm";
var CREDENTIAL_QUERY_PARAM = "X-Amz-Credential";
var AMZ_DATE_QUERY_PARAM = "X-Amz-Date";
var SIGNED_HEADERS_QUERY_PARAM = "X-Amz-SignedHeaders";
var EXPIRES_QUERY_PARAM = "X-Amz-Expires";
var SIGNATURE_QUERY_PARAM = "X-Amz-Signature";
var TOKEN_QUERY_PARAM = "X-Amz-Security-Token";
var AUTH_HEADER = "authorization";
var AMZ_DATE_HEADER = AMZ_DATE_QUERY_PARAM.toLowerCase();
var DATE_HEADER = "date";
var GENERATED_HEADERS = [AUTH_HEADER, AMZ_DATE_HEADER, DATE_HEADER];
var SIGNATURE_HEADER = SIGNATURE_QUERY_PARAM.toLowerCase();
var SHA256_HEADER = "x-amz-content-sha256";
var TOKEN_HEADER = TOKEN_QUERY_PARAM.toLowerCase();
var ALWAYS_UNSIGNABLE_HEADERS = {
  authorization: true,
  "cache-control": true,
  connection: true,
  expect: true,
  from: true,
  "keep-alive": true,
  "max-forwards": true,
  pragma: true,
  referer: true,
  te: true,
  trailer: true,
  "transfer-encoding": true,
  upgrade: true,
  "user-agent": true,
  "x-amzn-trace-id": true
};
var PROXY_HEADER_PATTERN = /^proxy-/;
var SEC_HEADER_PATTERN = /^sec-/;
var ALGORITHM_IDENTIFIER = "AWS4-HMAC-SHA256";
var EVENT_ALGORITHM_IDENTIFIER = "AWS4-HMAC-SHA256-PAYLOAD";
var UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD";
var MAX_CACHE_SIZE = 50;
var KEY_TYPE_IDENTIFIER = "aws4_request";
var MAX_PRESIGNED_TTL = 60 * 60 * 24 * 7;

// node_modules/@smithy/signature-v4/dist-es/getCanonicalQuery.js
var getCanonicalQuery = ({ query = {} }) => {
  const keys = [];
  const serialized = {};
  for (const key of Object.keys(query)) {
    if (key.toLowerCase() === SIGNATURE_HEADER) {
      continue;
    }
    const encodedKey = escapeUri(key);
    keys.push(encodedKey);
    const value = query[key];
    if (typeof value === "string") {
      serialized[encodedKey] = `${encodedKey}=${escapeUri(value)}`;
    } else if (Array.isArray(value)) {
      serialized[encodedKey] = value.slice(0).reduce((encoded, value2) => encoded.concat([`${encodedKey}=${escapeUri(value2)}`]), []).sort().join("&");
    }
  }
  return keys.sort().map((key) => serialized[key]).filter((serialized2) => serialized2).join("&");
};

// node_modules/@smithy/signature-v4/dist-es/utilDate.js
var iso8601 = (time2) => toDate(time2).toISOString().replace(/\.\d{3}Z$/, "Z");
var toDate = (time2) => {
  if (typeof time2 === "number") {
    return new Date(time2 * 1e3);
  }
  if (typeof time2 === "string") {
    if (Number(time2)) {
      return new Date(Number(time2) * 1e3);
    }
    return new Date(time2);
  }
  return time2;
};

// node_modules/@smithy/signature-v4/dist-es/SignatureV4Base.js
var SignatureV4Base = class {
  service;
  regionProvider;
  credentialProvider;
  sha256;
  uriEscapePath;
  applyChecksum;
  constructor({ applyChecksum, credentials, region, service, sha256, uriEscapePath = true }) {
    this.service = service;
    this.sha256 = sha256;
    this.uriEscapePath = uriEscapePath;
    this.applyChecksum = typeof applyChecksum === "boolean" ? applyChecksum : true;
    this.regionProvider = normalizeProvider(region);
    this.credentialProvider = normalizeProvider(credentials);
  }
  createCanonicalRequest(request, canonicalHeaders, payloadHash) {
    const sortedHeaders = Object.keys(canonicalHeaders).sort();
    return `${request.method}
${this.getCanonicalPath(request)}
${getCanonicalQuery(request)}
${sortedHeaders.map((name) => `${name}:${canonicalHeaders[name]}`).join("\n")}

${sortedHeaders.join(";")}
${payloadHash}`;
  }
  async createStringToSign(longDate, credentialScope, canonicalRequest, algorithmIdentifier) {
    const hash = new this.sha256();
    hash.update(toUint8Array(canonicalRequest));
    const hashedRequest = await hash.digest();
    return `${algorithmIdentifier}
${longDate}
${credentialScope}
${toHex(hashedRequest)}`;
  }
  getCanonicalPath({ path }) {
    if (this.uriEscapePath) {
      const normalizedPathSegments = [];
      for (const pathSegment of path.split("/")) {
        if (pathSegment?.length === 0)
          continue;
        if (pathSegment === ".")
          continue;
        if (pathSegment === "..") {
          normalizedPathSegments.pop();
        } else {
          normalizedPathSegments.push(pathSegment);
        }
      }
      const normalizedPath = `${path?.startsWith("/") ? "/" : ""}${normalizedPathSegments.join("/")}${normalizedPathSegments.length > 0 && path?.endsWith("/") ? "/" : ""}`;
      const doubleEncoded = escapeUri(normalizedPath);
      return doubleEncoded.replace(/%2F/g, "/");
    }
    return path;
  }
  validateResolvedCredentials(credentials) {
    if (typeof credentials !== "object" || typeof credentials.accessKeyId !== "string" || typeof credentials.secretAccessKey !== "string") {
      throw new Error("Resolved credential object is not valid");
    }
  }
  formatDate(now) {
    const longDate = iso8601(now).replace(/[\-:]/g, "");
    return {
      longDate,
      shortDate: longDate.slice(0, 8)
    };
  }
  getCanonicalHeaderList(headers) {
    return Object.keys(headers).sort().join(";");
  }
};

// node_modules/@smithy/signature-v4/dist-es/credentialDerivation.js
init_index_browser2();
var signingKeyCache = {};
var cacheQueue = [];
var createScope = (shortDate, region, service) => `${shortDate}/${region}/${service}/${KEY_TYPE_IDENTIFIER}`;
var getSigningKey = async (sha256Constructor, credentials, shortDate, region, service) => {
  const credsHash = await hmac(sha256Constructor, credentials.secretAccessKey, credentials.accessKeyId);
  const cacheKey = `${shortDate}:${region}:${service}:${toHex(credsHash)}:${credentials.sessionToken}`;
  if (cacheKey in signingKeyCache) {
    return signingKeyCache[cacheKey];
  }
  cacheQueue.push(cacheKey);
  while (cacheQueue.length > MAX_CACHE_SIZE) {
    delete signingKeyCache[cacheQueue.shift()];
  }
  let key = `AWS4${credentials.secretAccessKey}`;
  for (const signable of [shortDate, region, service, KEY_TYPE_IDENTIFIER]) {
    key = await hmac(sha256Constructor, key, signable);
  }
  return signingKeyCache[cacheKey] = key;
};
var hmac = (ctor, secret, data) => {
  const hash = new ctor(secret);
  hash.update(toUint8Array(data));
  return hash.digest();
};

// node_modules/@smithy/signature-v4/dist-es/getCanonicalHeaders.js
var getCanonicalHeaders = ({ headers }, unsignableHeaders, signableHeaders) => {
  const canonical = {};
  for (const headerName of Object.keys(headers).sort()) {
    if (headers[headerName] == void 0) {
      continue;
    }
    const canonicalHeaderName = headerName.toLowerCase();
    if (canonicalHeaderName in ALWAYS_UNSIGNABLE_HEADERS || unsignableHeaders?.has(canonicalHeaderName) || PROXY_HEADER_PATTERN.test(canonicalHeaderName) || SEC_HEADER_PATTERN.test(canonicalHeaderName)) {
      if (!signableHeaders || signableHeaders && !signableHeaders.has(canonicalHeaderName)) {
        continue;
      }
    }
    canonical[canonicalHeaderName] = headers[headerName].trim().replace(/\s+/g, " ");
  }
  return canonical;
};

// node_modules/@smithy/signature-v4/dist-es/getPayloadHash.js
init_index_browser2();
var getPayloadHash = async ({ headers, body }, hashConstructor) => {
  for (const headerName of Object.keys(headers)) {
    if (headerName.toLowerCase() === SHA256_HEADER) {
      return headers[headerName];
    }
  }
  if (body == void 0) {
    return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
  } else if (typeof body === "string" || ArrayBuffer.isView(body) || isArrayBuffer(body)) {
    const hashCtor = new hashConstructor();
    hashCtor.update(toUint8Array(body));
    return toHex(await hashCtor.digest());
  }
  return UNSIGNED_PAYLOAD;
};

// node_modules/@smithy/signature-v4/dist-es/headerUtil.js
var hasHeader = (soughtHeader, headers) => {
  soughtHeader = soughtHeader.toLowerCase();
  for (const headerName of Object.keys(headers)) {
    if (soughtHeader === headerName.toLowerCase()) {
      return true;
    }
  }
  return false;
};

// node_modules/@smithy/signature-v4/dist-es/moveHeadersToQuery.js
var moveHeadersToQuery = (request, options = {}) => {
  const { headers, query = {} } = HttpRequest.clone(request);
  for (const name of Object.keys(headers)) {
    const lname = name.toLowerCase();
    if (lname.slice(0, 6) === "x-amz-" && !options.unhoistableHeaders?.has(lname) || options.hoistableHeaders?.has(lname)) {
      query[name] = headers[name];
      delete headers[name];
    }
  }
  return {
    ...request,
    headers,
    query
  };
};

// node_modules/@smithy/signature-v4/dist-es/prepareRequest.js
var prepareRequest = (request) => {
  request = HttpRequest.clone(request);
  for (const headerName of Object.keys(request.headers)) {
    if (GENERATED_HEADERS.indexOf(headerName.toLowerCase()) > -1) {
      delete request.headers[headerName];
    }
  }
  return request;
};

// node_modules/@smithy/signature-v4/dist-es/SignatureV4.js
var SignatureV4 = class extends SignatureV4Base {
  headerFormatter = new HeaderFormatter();
  constructor({ applyChecksum, credentials, region, service, sha256, uriEscapePath = true }) {
    super({
      applyChecksum,
      credentials,
      region,
      service,
      sha256,
      uriEscapePath
    });
  }
  async presign(originalRequest, options = {}) {
    const { signingDate = /* @__PURE__ */ new Date(), expiresIn = 3600, unsignableHeaders, unhoistableHeaders, signableHeaders, hoistableHeaders, signingRegion, signingService } = options;
    const credentials = await this.credentialProvider();
    this.validateResolvedCredentials(credentials);
    const region = signingRegion ?? await this.regionProvider();
    const { longDate, shortDate } = this.formatDate(signingDate);
    if (expiresIn > MAX_PRESIGNED_TTL) {
      return Promise.reject("Signature version 4 presigned URLs must have an expiration date less than one week in the future");
    }
    const scope = createScope(shortDate, region, signingService ?? this.service);
    const request = moveHeadersToQuery(prepareRequest(originalRequest), { unhoistableHeaders, hoistableHeaders });
    if (credentials.sessionToken) {
      request.query[TOKEN_QUERY_PARAM] = credentials.sessionToken;
    }
    request.query[ALGORITHM_QUERY_PARAM] = ALGORITHM_IDENTIFIER;
    request.query[CREDENTIAL_QUERY_PARAM] = `${credentials.accessKeyId}/${scope}`;
    request.query[AMZ_DATE_QUERY_PARAM] = longDate;
    request.query[EXPIRES_QUERY_PARAM] = expiresIn.toString(10);
    const canonicalHeaders = getCanonicalHeaders(request, unsignableHeaders, signableHeaders);
    request.query[SIGNED_HEADERS_QUERY_PARAM] = this.getCanonicalHeaderList(canonicalHeaders);
    request.query[SIGNATURE_QUERY_PARAM] = await this.getSignature(longDate, scope, this.getSigningKey(credentials, region, shortDate, signingService), this.createCanonicalRequest(request, canonicalHeaders, await getPayloadHash(originalRequest, this.sha256)));
    return request;
  }
  async sign(toSign, options) {
    if (typeof toSign === "string") {
      return this.signString(toSign, options);
    } else if (toSign.headers && toSign.payload) {
      return this.signEvent(toSign, options);
    } else if (toSign.message) {
      return this.signMessage(toSign, options);
    } else {
      return this.signRequest(toSign, options);
    }
  }
  async signEvent({ headers, payload }, { signingDate = /* @__PURE__ */ new Date(), priorSignature, signingRegion, signingService, eventStreamCredentials }) {
    const region = signingRegion ?? await this.regionProvider();
    const { shortDate, longDate } = this.formatDate(signingDate);
    const scope = createScope(shortDate, region, signingService ?? this.service);
    const hashedPayload = await getPayloadHash({ headers: {}, body: payload }, this.sha256);
    const hash = new this.sha256();
    hash.update(headers);
    const hashedHeaders = toHex(await hash.digest());
    const stringToSign = [
      EVENT_ALGORITHM_IDENTIFIER,
      longDate,
      scope,
      priorSignature,
      hashedHeaders,
      hashedPayload
    ].join("\n");
    return this.signString(stringToSign, {
      signingDate,
      signingRegion: region,
      signingService,
      eventStreamCredentials
    });
  }
  async signMessage(signableMessage, { signingDate = /* @__PURE__ */ new Date(), signingRegion, signingService, eventStreamCredentials }) {
    const promise = this.signEvent({
      headers: this.headerFormatter.format(signableMessage.message.headers),
      payload: signableMessage.message.body
    }, {
      signingDate,
      signingRegion,
      signingService,
      priorSignature: signableMessage.priorSignature,
      eventStreamCredentials
    });
    return promise.then((signature) => {
      return { message: signableMessage.message, signature };
    });
  }
  async signString(stringToSign, { signingDate = /* @__PURE__ */ new Date(), signingRegion, signingService, eventStreamCredentials } = {}) {
    const credentials = eventStreamCredentials ?? await this.credentialProvider();
    this.validateResolvedCredentials(credentials);
    const region = signingRegion ?? await this.regionProvider();
    const { shortDate } = this.formatDate(signingDate);
    const hash = new this.sha256(await this.getSigningKey(credentials, region, shortDate, signingService));
    hash.update(toUint8Array(stringToSign));
    return toHex(await hash.digest());
  }
  async signRequest(requestToSign, { signingDate = /* @__PURE__ */ new Date(), signableHeaders, unsignableHeaders, signingRegion, signingService } = {}) {
    const credentials = await this.credentialProvider();
    this.validateResolvedCredentials(credentials);
    const region = signingRegion ?? await this.regionProvider();
    const request = prepareRequest(requestToSign);
    const { longDate, shortDate } = this.formatDate(signingDate);
    const scope = createScope(shortDate, region, signingService ?? this.service);
    request.headers[AMZ_DATE_HEADER] = longDate;
    if (credentials.sessionToken) {
      request.headers[TOKEN_HEADER] = credentials.sessionToken;
    }
    const payloadHash = await getPayloadHash(request, this.sha256);
    if (!hasHeader(SHA256_HEADER, request.headers) && this.applyChecksum) {
      request.headers[SHA256_HEADER] = payloadHash;
    }
    const canonicalHeaders = getCanonicalHeaders(request, unsignableHeaders, signableHeaders);
    const signature = await this.getSignature(longDate, scope, this.getSigningKey(credentials, region, shortDate, signingService), this.createCanonicalRequest(request, canonicalHeaders, payloadHash));
    request.headers[AUTH_HEADER] = `${ALGORITHM_IDENTIFIER} Credential=${credentials.accessKeyId}/${scope}, SignedHeaders=${this.getCanonicalHeaderList(canonicalHeaders)}, Signature=${signature}`;
    return request;
  }
  async getSignature(longDate, credentialScope, keyPromise, canonicalRequest) {
    const stringToSign = await this.createStringToSign(longDate, credentialScope, canonicalRequest, ALGORITHM_IDENTIFIER);
    const hash = new this.sha256(await keyPromise);
    hash.update(toUint8Array(stringToSign));
    return toHex(await hash.digest());
  }
  getSigningKey(credentials, region, shortDate, service) {
    return getSigningKey(this.sha256, credentials, shortDate, region, service || this.service);
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/httpAuthSchemes/aws_sdk/resolveAwsSdkSigV4Config.js
var resolveAwsSdkSigV4Config = (config) => {
  let inputCredentials = config.credentials;
  let isUserSupplied = !!config.credentials;
  let resolvedCredentials = void 0;
  Object.defineProperty(config, "credentials", {
    set(credentials) {
      if (credentials && credentials !== inputCredentials && credentials !== resolvedCredentials) {
        isUserSupplied = true;
      }
      inputCredentials = credentials;
      const memoizedProvider = normalizeCredentialProvider(config, {
        credentials: inputCredentials,
        credentialDefaultProvider: config.credentialDefaultProvider
      });
      const boundProvider = bindCallerConfig(config, memoizedProvider);
      if (isUserSupplied && !boundProvider.attributed) {
        const isCredentialObject = typeof inputCredentials === "object" && inputCredentials !== null;
        resolvedCredentials = async (options) => {
          const creds = await boundProvider(options);
          const attributedCreds = creds;
          if (isCredentialObject && (!attributedCreds.$source || Object.keys(attributedCreds.$source).length === 0)) {
            return setCredentialFeature(attributedCreds, "CREDENTIALS_CODE", "e");
          }
          return attributedCreds;
        };
        resolvedCredentials.memoized = boundProvider.memoized;
        resolvedCredentials.configBound = boundProvider.configBound;
        resolvedCredentials.attributed = true;
      } else {
        resolvedCredentials = boundProvider;
      }
    },
    get() {
      return resolvedCredentials;
    },
    enumerable: true,
    configurable: true
  });
  config.credentials = inputCredentials;
  const { signingEscapePath = true, systemClockOffset = config.systemClockOffset || 0, sha256 } = config;
  let signer;
  if (config.signer) {
    signer = normalizeProvider2(config.signer);
  } else if (config.regionInfoProvider) {
    signer = () => normalizeProvider2(config.region)().then(async (region) => [
      await config.regionInfoProvider(region, {
        useFipsEndpoint: await config.useFipsEndpoint(),
        useDualstackEndpoint: await config.useDualstackEndpoint()
      }) || {},
      region
    ]).then(([regionInfo, region]) => {
      const { signingRegion, signingService } = regionInfo;
      config.signingRegion = config.signingRegion || signingRegion || region;
      config.signingName = config.signingName || signingService || config.serviceId;
      const params = {
        ...config,
        credentials: config.credentials,
        region: config.signingRegion,
        service: config.signingName,
        sha256,
        uriEscapePath: signingEscapePath
      };
      const SignerCtor = config.signerConstructor || SignatureV4;
      return new SignerCtor(params);
    });
  } else {
    signer = async (authScheme) => {
      authScheme = Object.assign({}, {
        name: "sigv4",
        signingName: config.signingName || config.defaultSigningName,
        signingRegion: await normalizeProvider2(config.region)(),
        properties: {}
      }, authScheme);
      const signingRegion = authScheme.signingRegion;
      const signingService = authScheme.signingName;
      config.signingRegion = config.signingRegion || signingRegion;
      config.signingName = config.signingName || signingService || config.serviceId;
      const params = {
        ...config,
        credentials: config.credentials,
        region: config.signingRegion,
        service: config.signingName,
        sha256,
        uriEscapePath: signingEscapePath
      };
      const SignerCtor = config.signerConstructor || SignatureV4;
      return new SignerCtor(params);
    };
  }
  const resolvedConfig = Object.assign(config, {
    systemClockOffset,
    signingEscapePath,
    signer
  });
  return resolvedConfig;
};
function normalizeCredentialProvider(config, { credentials, credentialDefaultProvider }) {
  let credentialsProvider;
  if (credentials) {
    if (!credentials?.memoized) {
      credentialsProvider = memoizeIdentityProvider(credentials, isIdentityExpired, doesIdentityRequireRefresh);
    } else {
      credentialsProvider = credentials;
    }
  } else {
    if (credentialDefaultProvider) {
      credentialsProvider = normalizeProvider2(credentialDefaultProvider(Object.assign({}, config, {
        parentClientConfig: config
      })));
    } else {
      credentialsProvider = async () => {
        throw new Error("@aws-sdk/core::resolveAwsSdkSigV4Config - `credentials` not provided and no credentialDefaultProvider was configured.");
      };
    }
  }
  credentialsProvider.memoized = true;
  return credentialsProvider;
}
function bindCallerConfig(config, credentialsProvider) {
  if (credentialsProvider.configBound) {
    return credentialsProvider;
  }
  const fn = async (options) => credentialsProvider({ ...options, callerClientConfig: config });
  fn.memoized = credentialsProvider.memoized;
  fn.configBound = true;
  return fn;
}

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/ProtocolLib.js
var ProtocolLib = class {
  queryCompat;
  constructor(queryCompat = false) {
    this.queryCompat = queryCompat;
  }
  resolveRestContentType(defaultContentType, inputSchema) {
    const members = inputSchema.getMemberSchemas();
    const httpPayloadMember = Object.values(members).find((m2) => {
      return !!m2.getMergedTraits().httpPayload;
    });
    if (httpPayloadMember) {
      const mediaType = httpPayloadMember.getMergedTraits().mediaType;
      if (mediaType) {
        return mediaType;
      } else if (httpPayloadMember.isStringSchema()) {
        return "text/plain";
      } else if (httpPayloadMember.isBlobSchema()) {
        return "application/octet-stream";
      } else {
        return defaultContentType;
      }
    } else if (!inputSchema.isUnitSchema()) {
      const hasBody = Object.values(members).find((m2) => {
        const { httpQuery, httpQueryParams, httpHeader, httpLabel, httpPrefixHeaders } = m2.getMergedTraits();
        const noPrefixHeaders = httpPrefixHeaders === void 0;
        return !httpQuery && !httpQueryParams && !httpHeader && !httpLabel && noPrefixHeaders;
      });
      if (hasBody) {
        return defaultContentType;
      }
    }
  }
  async getErrorSchemaOrThrowBaseException(errorIdentifier, defaultNamespace, response, dataObject, metadata, getErrorSchema) {
    let namespace = defaultNamespace;
    let errorName = errorIdentifier;
    if (errorIdentifier.includes("#")) {
      [namespace, errorName] = errorIdentifier.split("#");
    }
    const errorMetadata = {
      $metadata: metadata,
      $fault: response.statusCode < 500 ? "client" : "server"
    };
    const registry = TypeRegistry.for(namespace);
    try {
      const errorSchema = getErrorSchema?.(registry, errorName) ?? registry.getSchema(errorIdentifier);
      return { errorSchema, errorMetadata };
    } catch (e2) {
      dataObject.message = dataObject.message ?? dataObject.Message ?? "UnknownError";
      const synthetic = TypeRegistry.for("smithy.ts.sdk.synthetic." + namespace);
      const baseExceptionSchema = synthetic.getBaseException();
      if (baseExceptionSchema) {
        const ErrorCtor = synthetic.getErrorCtor(baseExceptionSchema) ?? Error;
        throw this.decorateServiceException(Object.assign(new ErrorCtor({ name: errorName }), errorMetadata), dataObject);
      }
      throw this.decorateServiceException(Object.assign(new Error(errorName), errorMetadata), dataObject);
    }
  }
  decorateServiceException(exception, additions = {}) {
    if (this.queryCompat) {
      const msg = exception.Message ?? additions.Message;
      const error = decorateServiceException(exception, additions);
      if (msg) {
        error.message = msg;
      }
      error.Error = {
        ...error.Error,
        Type: error.Error.Type,
        Code: error.Error.Code,
        Message: error.Error.message ?? error.Error.Message ?? msg
      };
      const reqId = error.$metadata.requestId;
      if (reqId) {
        error.RequestId = reqId;
      }
      return error;
    }
    return decorateServiceException(exception, additions);
  }
  setQueryCompatError(output, response) {
    const queryErrorHeader = response.headers?.["x-amzn-query-error"];
    if (output !== void 0 && queryErrorHeader != null) {
      const [Code, Type] = queryErrorHeader.split(";");
      const entries = Object.entries(output);
      const Error2 = {
        Code,
        Type
      };
      Object.assign(output, Error2);
      for (const [k2, v2] of entries) {
        Error2[k2 === "message" ? "Message" : k2] = v2;
      }
      delete Error2.__type;
      output.Error = Error2;
    }
  }
  queryCompatOutput(queryCompatErrorData, errorData) {
    if (queryCompatErrorData.Error) {
      errorData.Error = queryCompatErrorData.Error;
    }
    if (queryCompatErrorData.Type) {
      errorData.Type = queryCompatErrorData.Type;
    }
    if (queryCompatErrorData.Code) {
      errorData.Code = queryCompatErrorData.Code;
    }
  }
  findQueryCompatibleError(registry, errorName) {
    try {
      return registry.getSchema(errorName);
    } catch (e2) {
      return registry.find((schema) => NormalizedSchema.of(schema).getMergedTraits().awsQueryError?.[0] === errorName);
    }
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/ConfigurableSerdeContext.js
var SerdeContextConfig = class {
  serdeContext;
  setSerdeContext(serdeContext) {
    this.serdeContext = serdeContext;
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/JsonShapeDeserializer.js
init_index_browser2();

// node_modules/@smithy/util-base64/dist-es/index.js
init_index_browser2();

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/structIterator.js
function* serializingStructIterator(ns, sourceObject) {
  if (ns.isUnitSchema()) {
    return;
  }
  const struct = ns.getSchema();
  for (let i2 = 0; i2 < struct[4].length; ++i2) {
    const key = struct[4][i2];
    const memberSchema = struct[5][i2];
    const memberNs = new NormalizedSchema([memberSchema, 0], key);
    if (!(key in sourceObject) && !memberNs.isIdempotencyToken()) {
      continue;
    }
    yield [key, memberNs];
  }
}
function* deserializingStructIterator(ns, sourceObject, nameTrait) {
  if (ns.isUnitSchema()) {
    return;
  }
  const struct = ns.getSchema();
  let keysRemaining = Object.keys(sourceObject).filter((k2) => k2 !== "__type").length;
  for (let i2 = 0; i2 < struct[4].length; ++i2) {
    if (keysRemaining === 0) {
      break;
    }
    const key = struct[4][i2];
    const memberSchema = struct[5][i2];
    const memberNs = new NormalizedSchema([memberSchema, 0], key);
    let serializationKey = key;
    if (nameTrait) {
      serializationKey = memberNs.getMergedTraits()[nameTrait] ?? key;
    }
    if (!(serializationKey in sourceObject)) {
      continue;
    }
    yield [key, memberNs];
    keysRemaining -= 1;
  }
}

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/UnionSerde.js
var UnionSerde = class {
  from;
  to;
  keys;
  constructor(from, to) {
    this.from = from;
    this.to = to;
    this.keys = new Set(Object.keys(this.from).filter((k2) => k2 !== "__type"));
  }
  mark(key) {
    this.keys.delete(key);
  }
  hasUnknown() {
    return this.keys.size === 1 && Object.keys(this.to).length === 0;
  }
  writeUnknown() {
    if (this.hasUnknown()) {
      const k2 = this.keys.values().next().value;
      const v2 = this.from[k2];
      this.to.$unknown = [k2, v2];
    }
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/jsonReviver.js
init_index_browser2();
function jsonReviver(key, value, context) {
  if (context?.source) {
    const numericString = context.source;
    if (typeof value === "number") {
      if (value > Number.MAX_SAFE_INTEGER || value < Number.MIN_SAFE_INTEGER || numericString !== String(value)) {
        const isFractional = numericString.includes(".");
        if (isFractional) {
          return new NumericValue(numericString, "bigDecimal");
        } else {
          return BigInt(numericString);
        }
      }
    }
  }
  return value;
}

// node_modules/@smithy/util-utf8/dist-es/index.js
init_index_browser2();

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/common.js
var collectBodyString = (streamBody, context) => collectBody(streamBody, context).then((body) => (context?.utf8Encoder ?? toUtf8)(body));

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/parseJsonBody.js
var parseJsonBody = (streamBody, context) => collectBodyString(streamBody, context).then((encoded) => {
  if (encoded.length) {
    try {
      return JSON.parse(encoded);
    } catch (e2) {
      if (e2?.name === "SyntaxError") {
        Object.defineProperty(e2, "$responseBodyText", {
          value: encoded
        });
      }
      throw e2;
    }
  }
  return {};
});
var loadRestJsonErrorCode = (output, data) => {
  const findKey = (object, key) => Object.keys(object).find((k2) => k2.toLowerCase() === key.toLowerCase());
  const sanitizeErrorCode = (rawValue) => {
    let cleanValue = rawValue;
    if (typeof cleanValue === "number") {
      cleanValue = cleanValue.toString();
    }
    if (cleanValue.indexOf(",") >= 0) {
      cleanValue = cleanValue.split(",")[0];
    }
    if (cleanValue.indexOf(":") >= 0) {
      cleanValue = cleanValue.split(":")[0];
    }
    if (cleanValue.indexOf("#") >= 0) {
      cleanValue = cleanValue.split("#")[1];
    }
    return cleanValue;
  };
  const headerKey = findKey(output.headers, "x-amzn-errortype");
  if (headerKey !== void 0) {
    return sanitizeErrorCode(output.headers[headerKey]);
  }
  if (data && typeof data === "object") {
    const codeKey = findKey(data, "code");
    if (codeKey && data[codeKey] !== void 0) {
      return sanitizeErrorCode(data[codeKey]);
    }
    if (data["__type"] !== void 0) {
      return sanitizeErrorCode(data["__type"]);
    }
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/JsonShapeDeserializer.js
var JsonShapeDeserializer = class extends SerdeContextConfig {
  settings;
  constructor(settings) {
    super();
    this.settings = settings;
  }
  async read(schema, data) {
    return this._read(schema, typeof data === "string" ? JSON.parse(data, jsonReviver) : await parseJsonBody(data, this.serdeContext));
  }
  readObject(schema, data) {
    return this._read(schema, data);
  }
  _read(schema, value) {
    const isObject = value !== null && typeof value === "object";
    const ns = NormalizedSchema.of(schema);
    if (isObject) {
      if (ns.isStructSchema()) {
        const union = ns.isUnionSchema();
        const out = {};
        let unionSerde;
        if (union) {
          unionSerde = new UnionSerde(value, out);
        }
        for (const [memberName, memberSchema] of deserializingStructIterator(ns, value, this.settings.jsonName ? "jsonName" : false)) {
          const fromKey = this.settings.jsonName ? memberSchema.getMergedTraits().jsonName ?? memberName : memberName;
          if (union) {
            unionSerde.mark(fromKey);
          }
          if (value[fromKey] != null) {
            out[memberName] = this._read(memberSchema, value[fromKey]);
          }
        }
        if (union) {
          unionSerde.writeUnknown();
        }
        return out;
      }
      if (Array.isArray(value) && ns.isListSchema()) {
        const listMember = ns.getValueSchema();
        const out = [];
        const sparse = !!ns.getMergedTraits().sparse;
        for (const item of value) {
          if (sparse || item != null) {
            out.push(this._read(listMember, item));
          }
        }
        return out;
      }
      if (ns.isMapSchema()) {
        const mapMember = ns.getValueSchema();
        const out = {};
        const sparse = !!ns.getMergedTraits().sparse;
        for (const [_k2, _v2] of Object.entries(value)) {
          if (sparse || _v2 != null) {
            out[_k2] = this._read(mapMember, _v2);
          }
        }
        return out;
      }
    }
    if (ns.isBlobSchema() && typeof value === "string") {
      return fromBase64(value);
    }
    const mediaType = ns.getMergedTraits().mediaType;
    if (ns.isStringSchema() && typeof value === "string" && mediaType) {
      const isJson = mediaType === "application/json" || mediaType.endsWith("+json");
      if (isJson) {
        return LazyJsonString.from(value);
      }
      return value;
    }
    if (ns.isTimestampSchema() && value != null) {
      const format2 = determineTimestampFormat(ns, this.settings);
      switch (format2) {
        case 5:
          return parseRfc3339DateTimeWithOffset(value);
        case 6:
          return parseRfc7231DateTime(value);
        case 7:
          return parseEpochTimestamp(value);
        default:
          console.warn("Missing timestamp format, parsing value with Date constructor:", value);
          return new Date(value);
      }
    }
    if (ns.isBigIntegerSchema() && (typeof value === "number" || typeof value === "string")) {
      return BigInt(value);
    }
    if (ns.isBigDecimalSchema() && value != void 0) {
      if (value instanceof NumericValue) {
        return value;
      }
      const untyped = value;
      if (untyped.type === "bigDecimal" && "string" in untyped) {
        return new NumericValue(untyped.string, untyped.type);
      }
      return new NumericValue(String(value), "bigDecimal");
    }
    if (ns.isNumericSchema() && typeof value === "string") {
      switch (value) {
        case "Infinity":
          return Infinity;
        case "-Infinity":
          return -Infinity;
        case "NaN":
          return NaN;
      }
      return value;
    }
    if (ns.isDocumentSchema()) {
      if (isObject) {
        const out = Array.isArray(value) ? [] : {};
        for (const [k2, v2] of Object.entries(value)) {
          if (v2 instanceof NumericValue) {
            out[k2] = v2;
          } else {
            out[k2] = this._read(ns, v2);
          }
        }
        return out;
      } else {
        return structuredClone(value);
      }
    }
    return value;
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/JsonShapeSerializer.js
init_index_browser2();

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/jsonReplacer.js
init_index_browser2();
var NUMERIC_CONTROL_CHAR = String.fromCharCode(925);
var JsonReplacer = class {
  values = /* @__PURE__ */ new Map();
  counter = 0;
  stage = 0;
  createReplacer() {
    if (this.stage === 1) {
      throw new Error("@aws-sdk/core/protocols - JsonReplacer already created.");
    }
    if (this.stage === 2) {
      throw new Error("@aws-sdk/core/protocols - JsonReplacer exhausted.");
    }
    this.stage = 1;
    return (key, value) => {
      if (value instanceof NumericValue) {
        const v2 = `${NUMERIC_CONTROL_CHAR + "nv" + this.counter++}_` + value.string;
        this.values.set(`"${v2}"`, value.string);
        return v2;
      }
      if (typeof value === "bigint") {
        const s2 = value.toString();
        const v2 = `${NUMERIC_CONTROL_CHAR + "b" + this.counter++}_` + s2;
        this.values.set(`"${v2}"`, s2);
        return v2;
      }
      return value;
    };
  }
  replaceInJson(json) {
    if (this.stage === 0) {
      throw new Error("@aws-sdk/core/protocols - JsonReplacer not created yet.");
    }
    if (this.stage === 2) {
      throw new Error("@aws-sdk/core/protocols - JsonReplacer exhausted.");
    }
    this.stage = 2;
    if (this.counter === 0) {
      return json;
    }
    for (const [key, value] of this.values) {
      json = json.replace(key, value);
    }
    return json;
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/JsonShapeSerializer.js
var JsonShapeSerializer = class extends SerdeContextConfig {
  settings;
  buffer;
  useReplacer = false;
  rootSchema;
  constructor(settings) {
    super();
    this.settings = settings;
  }
  write(schema, value) {
    this.rootSchema = NormalizedSchema.of(schema);
    this.buffer = this._write(this.rootSchema, value);
  }
  writeDiscriminatedDocument(schema, value) {
    this.write(schema, value);
    if (typeof this.buffer === "object") {
      this.buffer.__type = NormalizedSchema.of(schema).getName(true);
    }
  }
  flush() {
    const { rootSchema, useReplacer } = this;
    this.rootSchema = void 0;
    this.useReplacer = false;
    if (rootSchema?.isStructSchema() || rootSchema?.isDocumentSchema()) {
      if (!useReplacer) {
        return JSON.stringify(this.buffer);
      }
      const replacer = new JsonReplacer();
      return replacer.replaceInJson(JSON.stringify(this.buffer, replacer.createReplacer(), 0));
    }
    return this.buffer;
  }
  _write(schema, value, container) {
    const isObject = value !== null && typeof value === "object";
    const ns = NormalizedSchema.of(schema);
    if (isObject) {
      if (ns.isStructSchema()) {
        const out = {};
        for (const [memberName, memberSchema] of serializingStructIterator(ns, value)) {
          const serializableValue = this._write(memberSchema, value[memberName], ns);
          if (serializableValue !== void 0) {
            const jsonName = memberSchema.getMergedTraits().jsonName;
            const targetKey = this.settings.jsonName ? jsonName ?? memberName : memberName;
            out[targetKey] = serializableValue;
          }
        }
        if (ns.isUnionSchema() && Object.keys(out).length === 0) {
          const { $unknown } = value;
          if (Array.isArray($unknown)) {
            const [k2, v2] = $unknown;
            out[k2] = this._write(15, v2);
          }
        }
        return out;
      }
      if (Array.isArray(value) && ns.isListSchema()) {
        const listMember = ns.getValueSchema();
        const out = [];
        const sparse = !!ns.getMergedTraits().sparse;
        for (const item of value) {
          if (sparse || item != null) {
            out.push(this._write(listMember, item));
          }
        }
        return out;
      }
      if (ns.isMapSchema()) {
        const mapMember = ns.getValueSchema();
        const out = {};
        const sparse = !!ns.getMergedTraits().sparse;
        for (const [_k2, _v2] of Object.entries(value)) {
          if (sparse || _v2 != null) {
            out[_k2] = this._write(mapMember, _v2);
          }
        }
        return out;
      }
      if (value instanceof Uint8Array && (ns.isBlobSchema() || ns.isDocumentSchema())) {
        if (ns === this.rootSchema) {
          return value;
        }
        return (this.serdeContext?.base64Encoder ?? toBase64)(value);
      }
      if (value instanceof Date && (ns.isTimestampSchema() || ns.isDocumentSchema())) {
        const format2 = determineTimestampFormat(ns, this.settings);
        switch (format2) {
          case 5:
            return value.toISOString().replace(".000Z", "Z");
          case 6:
            return dateToUtcString(value);
          case 7:
            return value.getTime() / 1e3;
          default:
            console.warn("Missing timestamp format, using epoch seconds", value);
            return value.getTime() / 1e3;
        }
      }
      if (value instanceof NumericValue) {
        this.useReplacer = true;
      }
    }
    if (value === null && container?.isStructSchema()) {
      return void 0;
    }
    if (ns.isStringSchema()) {
      if (typeof value === "undefined" && ns.isIdempotencyToken()) {
        return generateIdempotencyToken();
      }
      const mediaType = ns.getMergedTraits().mediaType;
      if (value != null && mediaType) {
        const isJson = mediaType === "application/json" || mediaType.endsWith("+json");
        if (isJson) {
          return LazyJsonString.from(value);
        }
      }
      return value;
    }
    if (typeof value === "number" && ns.isNumericSchema()) {
      if (Math.abs(value) === Infinity || isNaN(value)) {
        return String(value);
      }
      return value;
    }
    if (typeof value === "string" && ns.isBlobSchema()) {
      if (ns === this.rootSchema) {
        return value;
      }
      return (this.serdeContext?.base64Encoder ?? toBase64)(value);
    }
    if (typeof value === "bigint") {
      this.useReplacer = true;
    }
    if (ns.isDocumentSchema()) {
      if (isObject) {
        const out = Array.isArray(value) ? [] : {};
        for (const [k2, v2] of Object.entries(value)) {
          if (v2 instanceof NumericValue) {
            this.useReplacer = true;
            out[k2] = v2;
          } else {
            out[k2] = this._write(ns, v2);
          }
        }
        return out;
      } else {
        return structuredClone(value);
      }
    }
    return value;
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/JsonCodec.js
var JsonCodec = class extends SerdeContextConfig {
  settings;
  constructor(settings) {
    super();
    this.settings = settings;
  }
  createSerializer() {
    const serializer = new JsonShapeSerializer(this.settings);
    serializer.setSerdeContext(this.serdeContext);
    return serializer;
  }
  createDeserializer() {
    const deserializer = new JsonShapeDeserializer(this.settings);
    deserializer.setSerdeContext(this.serdeContext);
    return deserializer;
  }
};

// node_modules/@aws-sdk/core/dist-es/submodules/protocols/json/AwsRestJsonProtocol.js
var AwsRestJsonProtocol = class extends HttpBindingProtocol {
  serializer;
  deserializer;
  codec;
  mixin = new ProtocolLib();
  constructor({ defaultNamespace }) {
    super({
      defaultNamespace
    });
    const settings = {
      timestampFormat: {
        useTrait: true,
        default: 7
      },
      httpBindings: true,
      jsonName: true
    };
    this.codec = new JsonCodec(settings);
    this.serializer = new HttpInterceptingShapeSerializer(this.codec.createSerializer(), settings);
    this.deserializer = new HttpInterceptingShapeDeserializer(this.codec.createDeserializer(), settings);
  }
  getShapeId() {
    return "aws.protocols#restJson1";
  }
  getPayloadCodec() {
    return this.codec;
  }
  setSerdeContext(serdeContext) {
    this.codec.setSerdeContext(serdeContext);
    super.setSerdeContext(serdeContext);
  }
  async serializeRequest(operationSchema, input, context) {
    const request = await super.serializeRequest(operationSchema, input, context);
    const inputSchema = NormalizedSchema.of(operationSchema.input);
    if (!request.headers["content-type"]) {
      const contentType = this.mixin.resolveRestContentType(this.getDefaultContentType(), inputSchema);
      if (contentType) {
        request.headers["content-type"] = contentType;
      }
    }
    if (request.body == null && request.headers["content-type"] === this.getDefaultContentType()) {
      request.body = "{}";
    }
    return request;
  }
  async deserializeResponse(operationSchema, context, response) {
    const output = await super.deserializeResponse(operationSchema, context, response);
    const outputSchema = NormalizedSchema.of(operationSchema.output);
    for (const [name, member2] of outputSchema.structIterator()) {
      if (member2.getMemberTraits().httpPayload && !(name in output)) {
        output[name] = null;
      }
    }
    return output;
  }
  async handleError(operationSchema, context, response, dataObject, metadata) {
    const errorIdentifier = loadRestJsonErrorCode(response, dataObject) ?? "Unknown";
    const { errorSchema, errorMetadata } = await this.mixin.getErrorSchemaOrThrowBaseException(errorIdentifier, this.options.defaultNamespace, response, dataObject, metadata);
    const ns = NormalizedSchema.of(errorSchema);
    const message = dataObject.message ?? dataObject.Message ?? "Unknown";
    const ErrorCtor = TypeRegistry.for(errorSchema[1]).getErrorCtor(errorSchema) ?? Error;
    const exception = new ErrorCtor(message);
    await this.deserializeHttpMessage(errorSchema, context, response, dataObject);
    const output = {};
    for (const [name, member2] of ns.structIterator()) {
      const target = member2.getMergedTraits().jsonName ?? name;
      output[name] = this.codec.createDeserializer().readObject(member2, dataObject[target]);
    }
    throw this.mixin.decorateServiceException(Object.assign(exception, errorMetadata, {
      $fault: ns.getMergedTraits().error,
      message
    }, output), dataObject);
  }
  getDefaultContentType() {
    return "application/json";
  }
};

// node_modules/@aws-sdk/middleware-user-agent/dist-es/check-features.js
var ACCOUNT_ID_ENDPOINT_REGEX = /\d{12}\.ddb/;
async function checkFeatures(context, config, args) {
  const request = args.request;
  if (request?.headers?.["smithy-protocol"] === "rpc-v2-cbor") {
    setFeature2(context, "PROTOCOL_RPC_V2_CBOR", "M");
  }
  if (typeof config.retryStrategy === "function") {
    const retryStrategy = await config.retryStrategy();
    if (typeof retryStrategy.acquireInitialRetryToken === "function") {
      if (retryStrategy.constructor?.name?.includes("Adaptive")) {
        setFeature2(context, "RETRY_MODE_ADAPTIVE", "F");
      } else {
        setFeature2(context, "RETRY_MODE_STANDARD", "E");
      }
    } else {
      setFeature2(context, "RETRY_MODE_LEGACY", "D");
    }
  }
  if (typeof config.accountIdEndpointMode === "function") {
    const endpointV2 = context.endpointV2;
    if (String(endpointV2?.url?.hostname).match(ACCOUNT_ID_ENDPOINT_REGEX)) {
      setFeature2(context, "ACCOUNT_ID_ENDPOINT", "O");
    }
    switch (await config.accountIdEndpointMode?.()) {
      case "disabled":
        setFeature2(context, "ACCOUNT_ID_MODE_DISABLED", "Q");
        break;
      case "preferred":
        setFeature2(context, "ACCOUNT_ID_MODE_PREFERRED", "P");
        break;
      case "required":
        setFeature2(context, "ACCOUNT_ID_MODE_REQUIRED", "R");
        break;
    }
  }
  const identity = context.__smithy_context?.selectedHttpAuthScheme?.identity;
  if (identity?.$source) {
    const credentials = identity;
    if (credentials.accountId) {
      setFeature2(context, "RESOLVED_ACCOUNT_ID", "T");
    }
    for (const [key, value] of Object.entries(credentials.$source ?? {})) {
      setFeature2(context, key, value);
    }
  }
}

// node_modules/@aws-sdk/middleware-user-agent/dist-es/constants.js
var USER_AGENT = "user-agent";
var X_AMZ_USER_AGENT = "x-amz-user-agent";
var SPACE = " ";
var UA_NAME_SEPARATOR = "/";
var UA_NAME_ESCAPE_REGEX = /[^!$%&'*+\-.^_`|~\w]/g;
var UA_VALUE_ESCAPE_REGEX = /[^!$%&'*+\-.^_`|~\w#]/g;
var UA_ESCAPE_CHAR = "-";

// node_modules/@aws-sdk/middleware-user-agent/dist-es/encode-features.js
var BYTE_LIMIT = 1024;
function encodeFeatures(features) {
  let buffer = "";
  for (const key in features) {
    const val = features[key];
    if (buffer.length + val.length + 1 <= BYTE_LIMIT) {
      if (buffer.length) {
        buffer += "," + val;
      } else {
        buffer += val;
      }
      continue;
    }
    break;
  }
  return buffer;
}

// node_modules/@aws-sdk/middleware-user-agent/dist-es/user-agent-middleware.js
var userAgentMiddleware = (options) => (next, context) => async (args) => {
  const { request } = args;
  if (!HttpRequest.isInstance(request)) {
    return next(args);
  }
  const { headers } = request;
  const userAgent = context?.userAgent?.map(escapeUserAgent) || [];
  const defaultUserAgent = (await options.defaultUserAgentProvider()).map(escapeUserAgent);
  await checkFeatures(context, options, args);
  const awsContext = context;
  defaultUserAgent.push(`m/${encodeFeatures(Object.assign({}, context.__smithy_context?.features, awsContext.__aws_sdk_context?.features))}`);
  const customUserAgent = options?.customUserAgent?.map(escapeUserAgent) || [];
  const appId = await options.userAgentAppId();
  if (appId) {
    defaultUserAgent.push(escapeUserAgent([`app`, `${appId}`]));
  }
  const prefix = getUserAgentPrefix();
  const sdkUserAgentValue = (prefix ? [prefix] : []).concat([...defaultUserAgent, ...userAgent, ...customUserAgent]).join(SPACE);
  const normalUAValue = [
    ...defaultUserAgent.filter((section) => section.startsWith("aws-sdk-")),
    ...customUserAgent
  ].join(SPACE);
  if (options.runtime !== "browser") {
    if (normalUAValue) {
      headers[X_AMZ_USER_AGENT] = headers[X_AMZ_USER_AGENT] ? `${headers[USER_AGENT]} ${normalUAValue}` : normalUAValue;
    }
    headers[USER_AGENT] = sdkUserAgentValue;
  } else {
    headers[X_AMZ_USER_AGENT] = sdkUserAgentValue;
  }
  return next({
    ...args,
    request
  });
};
var escapeUserAgent = (userAgentPair) => {
  const name = userAgentPair[0].split(UA_NAME_SEPARATOR).map((part) => part.replace(UA_NAME_ESCAPE_REGEX, UA_ESCAPE_CHAR)).join(UA_NAME_SEPARATOR);
  const version = userAgentPair[1]?.replace(UA_VALUE_ESCAPE_REGEX, UA_ESCAPE_CHAR);
  const prefixSeparatorIndex = name.indexOf(UA_NAME_SEPARATOR);
  const prefix = name.substring(0, prefixSeparatorIndex);
  let uaName = name.substring(prefixSeparatorIndex + 1);
  if (prefix === "api") {
    uaName = uaName.toLowerCase();
  }
  return [prefix, uaName, version].filter((item) => item && item.length > 0).reduce((acc, item, index) => {
    switch (index) {
      case 0:
        return item;
      case 1:
        return `${acc}/${item}`;
      default:
        return `${acc}#${item}`;
    }
  }, "");
};
var getUserAgentMiddlewareOptions = {
  name: "getUserAgentMiddleware",
  step: "build",
  priority: "low",
  tags: ["SET_USER_AGENT", "USER_AGENT"],
  override: true
};
var getUserAgentPlugin = (config) => ({
  applyToStack: (clientStack) => {
    clientStack.add(userAgentMiddleware(config), getUserAgentMiddlewareOptions);
  }
});

// node_modules/@smithy/middleware-endpoint/dist-es/index.js
init_index_browser();

// node_modules/@smithy/core/dist-es/submodules/retry/middleware-retry/isStreamingPayload/isStreamingPayload.browser.js
var isStreamingPayload = (request) => request?.body instanceof ReadableStream;

// node_modules/@smithy/core/dist-es/submodules/retry/middleware-retry/retryMiddleware.js
init_index_browser2();

// node_modules/@smithy/core/dist-es/submodules/retry/service-error-classification/constants.js
var THROTTLING_ERROR_CODES = [
  "BandwidthLimitExceeded",
  "EC2ThrottledException",
  "LimitExceededException",
  "PriorRequestNotComplete",
  "ProvisionedThroughputExceededException",
  "RequestLimitExceeded",
  "RequestThrottled",
  "RequestThrottledException",
  "SlowDown",
  "ThrottledException",
  "Throttling",
  "ThrottlingException",
  "TooManyRequestsException",
  "TransactionInProgressException"
];
var TRANSIENT_ERROR_CODES = ["TimeoutError", "RequestTimeout", "RequestTimeoutException"];
var TRANSIENT_ERROR_STATUS_CODES = [500, 502, 503, 504];
var NODEJS_TIMEOUT_ERROR_CODES = ["ECONNRESET", "ECONNREFUSED", "EPIPE", "ETIMEDOUT"];
var NODEJS_NETWORK_ERROR_CODES = ["EHOSTUNREACH", "ENETUNREACH", "ENOTFOUND", "EAI_AGAIN"];

// node_modules/@smithy/core/dist-es/submodules/retry/service-error-classification/service-error-classification.js
var isRetryableByTrait = (error) => error?.$retryable !== void 0;
var isClockSkewCorrectedError = (error) => error.$metadata?.clockSkewCorrected;
var isBrowserNetworkError = (error) => {
  const errorMessages = /* @__PURE__ */ new Set([
    "Failed to fetch",
    "NetworkError when attempting to fetch resource",
    "The Internet connection appears to be offline",
    "Load failed",
    "Network request failed"
  ]);
  const isValid = error && error instanceof TypeError;
  if (!isValid) {
    return false;
  }
  return errorMessages.has(error.message);
};
var isThrottlingError = (error) => error.$metadata?.httpStatusCode === 429 || THROTTLING_ERROR_CODES.includes(error.name) || error.$retryable?.throttling == true;
var isTransientError = (error, depth = 0) => isRetryableByTrait(error) || isClockSkewCorrectedError(error) || error.name === "InvalidSignatureException" && error.message?.includes("Signature expired") || TRANSIENT_ERROR_CODES.includes(error.name) || NODEJS_TIMEOUT_ERROR_CODES.includes(error?.code || "") || NODEJS_NETWORK_ERROR_CODES.includes(error?.code || "") || TRANSIENT_ERROR_STATUS_CODES.includes(error.$metadata?.httpStatusCode || 0) || isBrowserNetworkError(error) || isNodeJsHttp2TransientError(error) || error.cause !== void 0 && depth <= 10 && isTransientError(error.cause, depth + 1);
var isServerError = (error) => {
  if (error.$metadata?.httpStatusCode !== void 0) {
    const statusCode = error.$metadata.httpStatusCode;
    if (500 <= statusCode && statusCode <= 599 && !isTransientError(error)) {
      return true;
    }
    return false;
  }
  return false;
};
function isNodeJsHttp2TransientError(error) {
  return error.code === "ERR_HTTP2_STREAM_ERROR" && error.message.includes("NGHTTP2_REFUSED_STREAM");
}

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/constants.js
var MAXIMUM_RETRY_DELAY = 20 * 1e3;
var INITIAL_RETRY_TOKENS = 500;
var NO_RETRY_INCREMENT = 1;
var INVOCATION_ID_HEADER = "amz-sdk-invocation-id";
var REQUEST_HEADER = "amz-sdk-request";

// node_modules/@smithy/core/dist-es/submodules/retry/middleware-retry/parseRetryAfterHeader.js
init_index_browser2();
function parseRetryAfterHeader(response, logger2) {
  if (!HttpResponse.isInstance(response)) {
    return;
  }
  for (const header of Object.keys(response.headers)) {
    const h2 = header.toLowerCase();
    if (h2 === "retry-after") {
      const retryAfter = response.headers[header];
      let retryAfterSeconds = NaN;
      if (retryAfter.endsWith("GMT")) {
        try {
          const date2 = parseRfc7231DateTime(retryAfter);
          retryAfterSeconds = (date2.getTime() - Date.now()) / 1e3;
        } catch (e2) {
          logger2?.trace?.("Failed to parse retry-after header");
          logger2?.trace?.(e2);
        }
      } else if (retryAfter.match(/ GMT, ((\d+)|(\d+\.\d+))$/)) {
        retryAfterSeconds = Number(retryAfter.match(/ GMT, ([\d.]+)$/)?.[1]);
      } else if (retryAfter.match(/^((\d+)|(\d+\.\d+))$/)) {
        retryAfterSeconds = Number(retryAfter);
      } else if (Date.parse(retryAfter) >= Date.now()) {
        retryAfterSeconds = (Date.parse(retryAfter) - Date.now()) / 1e3;
      }
      if (isNaN(retryAfterSeconds)) {
        return;
      }
      return new Date(Date.now() + retryAfterSeconds * 1e3);
    } else if (h2 === "x-amz-retry-after") {
      const v2 = response.headers[header];
      const backoffMilliseconds = Number(v2);
      if (isNaN(backoffMilliseconds)) {
        logger2?.trace?.(`Failed to parse x-amz-retry-after=${v2}`);
        return;
      }
      return new Date(Date.now() + backoffMilliseconds);
    }
  }
}

// node_modules/@smithy/core/dist-es/submodules/retry/middleware-retry/util.js
var asSdkError = (error) => {
  if (error instanceof Error)
    return error;
  if (error instanceof Object)
    return Object.assign(new Error(), error);
  if (typeof error === "string")
    return new Error(error);
  return new Error(`AWS SDK error wrapper for ${error}`);
};

// node_modules/@smithy/core/dist-es/submodules/retry/middleware-retry/retryMiddleware.js
function bindRetryMiddleware(isStreamingPayload2) {
  return (options) => (next, context) => async (args) => {
    let retryStrategy = await options.retryStrategy();
    const maxAttempts = await options.maxAttempts();
    if (isRetryStrategyV2(retryStrategy)) {
      retryStrategy = retryStrategy;
      let retryToken = await retryStrategy.acquireInitialRetryToken((context["partition_id"] ?? "") + (context.__retryLongPoll ? ":longpoll" : ""));
      let lastError = new Error();
      let attempts = 0;
      let totalRetryDelay = 0;
      const { request } = args;
      const isRequest = HttpRequest.isInstance(request);
      if (isRequest) {
        request.headers[INVOCATION_ID_HEADER] = v4();
      }
      while (true) {
        try {
          if (isRequest) {
            request.headers[REQUEST_HEADER] = `attempt=${attempts + 1}; max=${maxAttempts}`;
          }
          const { response, output } = await next(args);
          retryStrategy.recordSuccess(retryToken);
          output.$metadata.attempts = attempts + 1;
          output.$metadata.totalRetryDelay = totalRetryDelay;
          return { response, output };
        } catch (e2) {
          const retryErrorInfo = getRetryErrorInfo(e2, options.logger);
          lastError = asSdkError(e2);
          if (isRequest && isStreamingPayload2(request)) {
            (context.logger instanceof NoOpLogger ? console : context.logger)?.warn("An error was encountered in a non-retryable streaming request.");
            throw lastError;
          }
          try {
            retryToken = await retryStrategy.refreshRetryTokenForRetry(retryToken, retryErrorInfo);
          } catch (refreshError) {
            if (!lastError.$metadata) {
              lastError.$metadata = {};
            }
            lastError.$metadata.attempts = attempts + 1;
            lastError.$metadata.totalRetryDelay = totalRetryDelay;
            throw lastError;
          }
          attempts = retryToken.getRetryCount();
          const delay = retryToken.getRetryDelay();
          totalRetryDelay += (retryToken?.$retryLog?.acquisitionDelay ?? 0) + delay;
          if (delay > 0) {
            await cooldown(delay);
          }
        }
      }
    } else {
      retryStrategy = retryStrategy;
      if (retryStrategy?.mode) {
        context.userAgent = [...context.userAgent || [], ["cfg/retry-mode", retryStrategy.mode]];
      }
      return retryStrategy.retry(next, args);
    }
  };
}
var cooldown = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
var isRetryStrategyV2 = (retryStrategy) => typeof retryStrategy.acquireInitialRetryToken !== "undefined" && typeof retryStrategy.refreshRetryTokenForRetry !== "undefined" && typeof retryStrategy.recordSuccess !== "undefined";
var getRetryErrorInfo = (error, logger2) => {
  const errorInfo = {
    error,
    errorType: getRetryErrorType(error)
  };
  const retryAfterHint = parseRetryAfterHeader(error.$response, logger2);
  if (retryAfterHint) {
    errorInfo.retryAfterHint = retryAfterHint;
  }
  return errorInfo;
};
var getRetryErrorType = (error) => {
  if (isThrottlingError(error))
    return "THROTTLING";
  if (isTransientError(error))
    return "TRANSIENT";
  if (isServerError(error))
    return "SERVER_ERROR";
  return "CLIENT_ERROR";
};
var retryMiddlewareOptions = {
  name: "retryMiddleware",
  tags: ["RETRY"],
  step: "finalizeRequest",
  priority: "high",
  override: true
};
function bindGetRetryPlugin(isStreamingPayload2) {
  const retryMiddleware2 = bindRetryMiddleware(isStreamingPayload2);
  return (options) => ({
    applyToStack: (clientStack) => {
      clientStack.add(retryMiddleware2(options), retryMiddlewareOptions);
    }
  });
}

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/DefaultRateLimiter.js
var DefaultRateLimiter = class _DefaultRateLimiter {
  static setTimeoutFn = (fn, delay) => setTimeout(fn, delay);
  beta;
  minCapacity;
  minFillRate;
  scaleConstant;
  smooth;
  enabled = false;
  availableTokens = 0;
  lastMaxRate = 0;
  measuredTxRate = 0;
  requestCount = 0;
  fillRate;
  lastThrottleTime;
  lastTimestamp = 0;
  lastTxRateBucket;
  maxCapacity;
  timeWindow = 0;
  constructor(options) {
    this.beta = options?.beta ?? 0.7;
    this.minCapacity = options?.minCapacity ?? 1;
    this.minFillRate = options?.minFillRate ?? 0.5;
    this.scaleConstant = options?.scaleConstant ?? 0.4;
    this.smooth = options?.smooth ?? 0.8;
    this.lastThrottleTime = this.getCurrentTimeInSeconds();
    this.lastTxRateBucket = Math.floor(this.getCurrentTimeInSeconds());
    this.fillRate = this.minFillRate;
    this.maxCapacity = this.minCapacity;
  }
  async getSendToken() {
    return this.acquireTokenBucket(1);
  }
  updateClientSendingRate(response) {
    let calculatedRate;
    this.updateMeasuredRate();
    const retryErrorInfo = response;
    const isThrottling = retryErrorInfo?.errorType === "THROTTLING" || isThrottlingError(retryErrorInfo?.error ?? response);
    if (isThrottling) {
      const rateToUse = !this.enabled ? this.measuredTxRate : Math.min(this.measuredTxRate, this.fillRate);
      this.lastMaxRate = rateToUse;
      this.calculateTimeWindow();
      this.lastThrottleTime = this.getCurrentTimeInSeconds();
      calculatedRate = this.cubicThrottle(rateToUse);
      this.enableTokenBucket();
    } else {
      this.calculateTimeWindow();
      calculatedRate = this.cubicSuccess(this.getCurrentTimeInSeconds());
    }
    const newRate = Math.min(calculatedRate, 2 * this.measuredTxRate);
    this.updateTokenBucketRate(newRate);
  }
  getCurrentTimeInSeconds() {
    return Date.now() / 1e3;
  }
  async acquireTokenBucket(amount) {
    if (!this.enabled) {
      return;
    }
    this.refillTokenBucket();
    while (amount > this.availableTokens) {
      const delay = (amount - this.availableTokens) / this.fillRate * 1e3;
      await new Promise((resolve) => _DefaultRateLimiter.setTimeoutFn(resolve, delay));
      this.refillTokenBucket();
    }
    this.availableTokens = this.availableTokens - amount;
  }
  refillTokenBucket() {
    const timestamp = this.getCurrentTimeInSeconds();
    if (!this.lastTimestamp) {
      this.lastTimestamp = timestamp;
      return;
    }
    const fillAmount = (timestamp - this.lastTimestamp) * this.fillRate;
    this.availableTokens = Math.min(this.maxCapacity, this.availableTokens + fillAmount);
    this.lastTimestamp = timestamp;
  }
  calculateTimeWindow() {
    this.timeWindow = this.getPrecise(Math.pow(this.lastMaxRate * (1 - this.beta) / this.scaleConstant, 1 / 3));
  }
  cubicThrottle(rateToUse) {
    return this.getPrecise(rateToUse * this.beta);
  }
  cubicSuccess(timestamp) {
    return this.getPrecise(this.scaleConstant * Math.pow(timestamp - this.lastThrottleTime - this.timeWindow, 3) + this.lastMaxRate);
  }
  enableTokenBucket() {
    this.enabled = true;
  }
  updateTokenBucketRate(newRate) {
    this.refillTokenBucket();
    this.fillRate = Math.max(newRate, this.minFillRate);
    this.maxCapacity = Math.max(newRate, this.minCapacity);
    this.availableTokens = Math.min(this.availableTokens, this.maxCapacity);
  }
  updateMeasuredRate() {
    const t2 = this.getCurrentTimeInSeconds();
    const timeBucket = Math.floor(t2 * 2) / 2;
    this.requestCount++;
    if (timeBucket > this.lastTxRateBucket) {
      const currentRate = this.requestCount / (timeBucket - this.lastTxRateBucket);
      this.measuredTxRate = this.getPrecise(currentRate * this.smooth + this.measuredTxRate * (1 - this.smooth));
      this.requestCount = 0;
      this.lastTxRateBucket = timeBucket;
    }
  }
  getPrecise(num) {
    return parseFloat(num.toFixed(8));
  }
};

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/retries-2026-config.js
var Retry = class _Retry {
  static v2026 = typeof process !== "undefined" && process.env?.SMITHY_NEW_RETRIES_2026 === "true";
  static delay() {
    return _Retry.v2026 ? 50 : 100;
  }
  static throttlingDelay() {
    return _Retry.v2026 ? 1e3 : 500;
  }
  static cost() {
    return _Retry.v2026 ? 14 : 5;
  }
  static throttlingCost() {
    return _Retry.v2026 ? 5 : 10;
  }
  static modifiedCostType() {
    return _Retry.v2026 ? "THROTTLING" : "TRANSIENT";
  }
};

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/DefaultRetryBackoffStrategy.js
var DefaultRetryBackoffStrategy = class {
  x = Retry.delay();
  computeNextBackoffDelay(i2) {
    const b2 = Math.random();
    const r2 = 2;
    const t_i = b2 * Math.min(this.x * r2 ** i2, MAXIMUM_RETRY_DELAY);
    return Math.floor(t_i);
  }
  setDelayBase(delay) {
    this.x = delay;
  }
};

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/DefaultRetryToken.js
var DefaultRetryToken = class {
  delay;
  count;
  cost;
  longPoll;
  $retryLog = {
    acquisitionDelay: 0
  };
  constructor(delay, count, cost, longPoll) {
    this.delay = delay;
    this.count = count;
    this.cost = cost;
    this.longPoll = longPoll;
  }
  getRetryCount() {
    return this.count;
  }
  getRetryDelay() {
    return Math.min(MAXIMUM_RETRY_DELAY, this.delay);
  }
  getRetryCost() {
    return this.cost;
  }
  isLongPoll() {
    return this.longPoll;
  }
};

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/config.js
var RETRY_MODES;
(function(RETRY_MODES2) {
  RETRY_MODES2["STANDARD"] = "standard";
  RETRY_MODES2["ADAPTIVE"] = "adaptive";
})(RETRY_MODES || (RETRY_MODES = {}));
var DEFAULT_MAX_ATTEMPTS = 3;
var DEFAULT_RETRY_MODE = RETRY_MODES.STANDARD;

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/StandardRetryStrategy.js
var refusal = {
  incompatible: 1,
  attempts: 2,
  capacity: 3
};
var StandardRetryStrategy = class {
  mode = RETRY_MODES.STANDARD;
  retryBackoffStrategy;
  capacity = INITIAL_RETRY_TOKENS;
  maxAttemptsProvider;
  baseDelay;
  constructor(arg1) {
    if (typeof arg1 === "number") {
      this.maxAttemptsProvider = async () => arg1;
    } else if (typeof arg1 === "function") {
      this.maxAttemptsProvider = arg1;
    } else if (arg1 && typeof arg1 === "object") {
      this.maxAttemptsProvider = async () => arg1.maxAttempts;
      this.baseDelay = arg1.baseDelay;
      this.retryBackoffStrategy = arg1.backoff;
    }
    this.maxAttemptsProvider ??= async () => DEFAULT_MAX_ATTEMPTS;
    this.baseDelay ??= Retry.delay();
    this.retryBackoffStrategy ??= new DefaultRetryBackoffStrategy();
  }
  async acquireInitialRetryToken(retryTokenScope) {
    return new DefaultRetryToken(Retry.delay(), 0, void 0, Retry.v2026 && retryTokenScope.includes(":longpoll"));
  }
  async refreshRetryTokenForRetry(token, errorInfo) {
    const maxAttempts = await this.getMaxAttempts();
    const retryCode = this.retryCode(token, errorInfo, maxAttempts);
    const shouldRetry = retryCode === 0;
    const isLongPoll = token.isLongPoll?.();
    if (shouldRetry || isLongPoll) {
      const errorType = errorInfo.errorType;
      this.retryBackoffStrategy.setDelayBase(errorType === "THROTTLING" ? Retry.throttlingDelay() : this.baseDelay);
      const delayFromErrorType = this.retryBackoffStrategy.computeNextBackoffDelay(token.getRetryCount());
      let retryDelay = delayFromErrorType;
      if (errorInfo.retryAfterHint instanceof Date) {
        retryDelay = Math.max(delayFromErrorType, Math.min(errorInfo.retryAfterHint.getTime() - Date.now(), delayFromErrorType + 5e3));
      }
      if (!shouldRetry) {
        const longPollBackoff = Retry.v2026 && retryCode === refusal.capacity && isLongPoll ? retryDelay : 0;
        if (longPollBackoff > 0) {
          await new Promise((r2) => setTimeout(r2, longPollBackoff));
        }
      } else {
        const capacityCost = this.getCapacityCost(errorType);
        this.capacity -= capacityCost;
        const nextToken = new DefaultRetryToken(0, token.getRetryCount() + 1, capacityCost, token.isLongPoll?.() ?? false);
        await new Promise((r2) => setTimeout(r2, retryDelay));
        nextToken.$retryLog.acquisitionDelay = retryDelay;
        return nextToken;
      }
    }
    throw new Error("No retry token available");
  }
  recordSuccess(token) {
    this.capacity = Math.min(INITIAL_RETRY_TOKENS, this.capacity + (token.getRetryCost() ?? NO_RETRY_INCREMENT));
  }
  getCapacity() {
    return this.capacity;
  }
  async maxAttempts() {
    return this.maxAttemptsProvider();
  }
  async getMaxAttempts() {
    try {
      return await this.maxAttemptsProvider();
    } catch (error) {
      console.warn(`Max attempts provider could not resolve. Using default of ${DEFAULT_MAX_ATTEMPTS}`);
      return DEFAULT_MAX_ATTEMPTS;
    }
  }
  retryCode(tokenToRenew, errorInfo, maxAttempts) {
    const attempts = tokenToRenew.getRetryCount() + 1;
    const retryableStatus = this.isRetryableError(errorInfo.errorType) ? 0 : refusal.incompatible;
    const attemptStatus = attempts < maxAttempts ? 0 : refusal.attempts;
    const capacityStatus = this.capacity >= this.getCapacityCost(errorInfo.errorType) ? 0 : refusal.capacity;
    return retryableStatus || attemptStatus || capacityStatus;
  }
  getCapacityCost(errorType) {
    return errorType === Retry.modifiedCostType() ? Retry.throttlingCost() : Retry.cost();
  }
  isRetryableError(errorType) {
    return errorType === "THROTTLING" || errorType === "TRANSIENT";
  }
};

// node_modules/@smithy/core/dist-es/submodules/retry/util-retry/AdaptiveRetryStrategy.js
var AdaptiveRetryStrategy = class {
  mode = RETRY_MODES.ADAPTIVE;
  rateLimiter;
  standardRetryStrategy;
  constructor(maxAttemptsProvider, options) {
    const { rateLimiter } = options ?? {};
    this.rateLimiter = rateLimiter ?? new DefaultRateLimiter();
    this.standardRetryStrategy = options ? new StandardRetryStrategy({
      maxAttempts: typeof maxAttemptsProvider === "number" ? maxAttemptsProvider : 3,
      ...options
    }) : new StandardRetryStrategy(maxAttemptsProvider);
  }
  async acquireInitialRetryToken(retryTokenScope) {
    const token = await this.standardRetryStrategy.acquireInitialRetryToken(retryTokenScope);
    await this.rateLimiter.getSendToken();
    return token;
  }
  async refreshRetryTokenForRetry(tokenToRenew, errorInfo) {
    this.rateLimiter.updateClientSendingRate(errorInfo);
    const token = await this.standardRetryStrategy.refreshRetryTokenForRetry(tokenToRenew, errorInfo);
    await this.rateLimiter.getSendToken();
    return token;
  }
  recordSuccess(token) {
    this.rateLimiter.updateClientSendingRate({});
    this.standardRetryStrategy.recordSuccess(token);
  }
  async maxAttemptsProvider() {
    return this.standardRetryStrategy.maxAttempts();
  }
};

// node_modules/@smithy/core/dist-es/submodules/retry/middleware-retry/configurations.js
var resolveRetryConfig = (input, defaults) => {
  const { retryStrategy, retryMode } = input;
  const { defaultMaxAttempts = DEFAULT_MAX_ATTEMPTS, defaultBaseDelay = Retry.delay() } = defaults ?? {};
  const maxAttemptsProvider = normalizeProvider(input.maxAttempts ?? defaultMaxAttempts);
  let controller = retryStrategy ? Promise.resolve(retryStrategy) : void 0;
  const getDefault = async () => {
    const maxAttempts = await maxAttemptsProvider();
    const adaptive = await normalizeProvider(retryMode)() === RETRY_MODES.ADAPTIVE;
    if (adaptive) {
      return new AdaptiveRetryStrategy(maxAttemptsProvider, {
        maxAttempts,
        baseDelay: defaultBaseDelay
      });
    }
    return new StandardRetryStrategy({
      maxAttempts,
      baseDelay: defaultBaseDelay
    });
  };
  return Object.assign(input, {
    maxAttempts: maxAttemptsProvider,
    retryStrategy: () => controller ??= getDefault()
  });
};

// node_modules/@smithy/core/dist-es/submodules/retry/index.browser.js
var retryMiddleware = bindRetryMiddleware(isStreamingPayload);
var getRetryPlugin = bindGetRetryPlugin(isStreamingPayload);

// node_modules/@aws-sdk/client-bedrock/dist-es/auth/httpAuthSchemeProvider.js
var defaultBedrockHttpAuthSchemeParametersProvider = async (config, context, input) => {
  return {
    operation: getSmithyContext(context).operation,
    region: await normalizeProvider(config.region)() || (() => {
      throw new Error("expected `region` to be configured for `aws.auth#sigv4`");
    })()
  };
};
function createAwsAuthSigv4HttpAuthOption(authParameters) {
  return {
    schemeId: "aws.auth#sigv4",
    signingProperties: {
      name: "bedrock",
      region: authParameters.region
    },
    propertiesExtractor: (config, context) => ({
      signingProperties: {
        config,
        context
      }
    })
  };
}
function createSmithyApiHttpBearerAuthHttpAuthOption(authParameters) {
  return {
    schemeId: "smithy.api#httpBearerAuth",
    propertiesExtractor: ({ profile, filepath, configFilepath, ignoreCache }, context) => ({
      identityProperties: {
        profile,
        filepath,
        configFilepath,
        ignoreCache
      }
    })
  };
}
var defaultBedrockHttpAuthSchemeProvider = (authParameters) => {
  const options = [];
  switch (authParameters.operation) {
    default: {
      options.push(createAwsAuthSigv4HttpAuthOption(authParameters));
      options.push(createSmithyApiHttpBearerAuthHttpAuthOption(authParameters));
    }
  }
  return options;
};
var resolveHttpAuthSchemeConfig = (config) => {
  const token = memoizeIdentityProvider(config.token, isIdentityExpired, doesIdentityRequireRefresh);
  const config_0 = resolveAwsSdkSigV4Config(config);
  return Object.assign(config_0, {
    authSchemePreference: normalizeProvider(config.authSchemePreference ?? []),
    token
  });
};

// node_modules/@aws-sdk/client-bedrock/dist-es/endpoint/EndpointParameters.js
var resolveClientEndpointParameters = (options) => {
  return Object.assign(options, {
    useDualstackEndpoint: options.useDualstackEndpoint ?? false,
    useFipsEndpoint: options.useFipsEndpoint ?? false,
    defaultSigningName: "bedrock"
  });
};
var commonParams = {
  UseFIPS: { type: "builtInParams", name: "useFipsEndpoint" },
  Endpoint: { type: "builtInParams", name: "endpoint" },
  Region: { type: "builtInParams", name: "region" },
  UseDualStack: { type: "builtInParams", name: "useDualstackEndpoint" }
};

// node_modules/@aws-sdk/client-bedrock/package.json
var package_default = {
  name: "@aws-sdk/client-bedrock",
  description: "AWS SDK for JavaScript Bedrock Client for Node.js, Browser and React Native",
  version: "3.967.0",
  scripts: {
    build: "concurrently 'yarn:build:types' 'yarn:build:es' && yarn build:cjs",
    "build:cjs": "node ../../scripts/compilation/inline client-bedrock",
    "build:es": "tsc -p tsconfig.es.json",
    "build:include:deps": 'yarn g:turbo run build -F="$npm_package_name"',
    "build:types": "tsc -p tsconfig.types.json",
    "build:types:downlevel": "downlevel-dts dist-types dist-types/ts3.4",
    clean: "rimraf ./dist-* && rimraf *.tsbuildinfo",
    "extract:docs": "api-extractor run --local",
    "generate:client": "node ../../scripts/generate-clients/single-service --solo bedrock",
    "test:index": "tsc --noEmit ./test/index-types.ts && node ./test/index-objects.spec.mjs"
  },
  main: "./dist-cjs/index.js",
  types: "./dist-types/index.d.ts",
  module: "./dist-es/index.js",
  sideEffects: false,
  dependencies: {
    "@aws-crypto/sha256-browser": "5.2.0",
    "@aws-crypto/sha256-js": "5.2.0",
    "@aws-sdk/core": "3.967.0",
    "@aws-sdk/credential-provider-node": "3.967.0",
    "@aws-sdk/middleware-host-header": "3.965.0",
    "@aws-sdk/middleware-logger": "3.965.0",
    "@aws-sdk/middleware-recursion-detection": "3.965.0",
    "@aws-sdk/middleware-user-agent": "3.967.0",
    "@aws-sdk/region-config-resolver": "3.965.0",
    "@aws-sdk/token-providers": "3.967.0",
    "@aws-sdk/types": "3.965.0",
    "@aws-sdk/util-endpoints": "3.965.0",
    "@aws-sdk/util-user-agent-browser": "3.965.0",
    "@aws-sdk/util-user-agent-node": "3.967.0",
    "@smithy/config-resolver": "^4.4.5",
    "@smithy/core": "^3.20.2",
    "@smithy/fetch-http-handler": "^5.3.8",
    "@smithy/hash-node": "^4.2.7",
    "@smithy/invalid-dependency": "^4.2.7",
    "@smithy/middleware-content-length": "^4.2.7",
    "@smithy/middleware-endpoint": "^4.4.3",
    "@smithy/middleware-retry": "^4.4.19",
    "@smithy/middleware-serde": "^4.2.8",
    "@smithy/middleware-stack": "^4.2.7",
    "@smithy/node-config-provider": "^4.3.7",
    "@smithy/node-http-handler": "^4.4.7",
    "@smithy/protocol-http": "^5.3.7",
    "@smithy/smithy-client": "^4.10.4",
    "@smithy/types": "^4.11.0",
    "@smithy/url-parser": "^4.2.7",
    "@smithy/util-base64": "^4.3.0",
    "@smithy/util-body-length-browser": "^4.2.0",
    "@smithy/util-body-length-node": "^4.2.1",
    "@smithy/util-defaults-mode-browser": "^4.3.18",
    "@smithy/util-defaults-mode-node": "^4.2.21",
    "@smithy/util-endpoints": "^3.2.7",
    "@smithy/util-middleware": "^4.2.7",
    "@smithy/util-retry": "^4.2.7",
    "@smithy/util-utf8": "^4.2.0",
    tslib: "^2.6.2"
  },
  devDependencies: {
    "@tsconfig/node18": "18.2.4",
    "@types/node": "^18.19.69",
    concurrently: "7.0.0",
    "downlevel-dts": "0.10.1",
    rimraf: "5.0.10",
    typescript: "~5.8.3"
  },
  engines: {
    node: ">=18.0.0"
  },
  typesVersions: {
    "<4.0": {
      "dist-types/*": [
        "dist-types/ts3.4/*"
      ]
    }
  },
  files: [
    "dist-*/**"
  ],
  author: {
    name: "AWS SDK for JavaScript Team",
    url: "https://aws.amazon.com/javascript/"
  },
  license: "Apache-2.0",
  browser: {
    "./dist-es/runtimeConfig": "./dist-es/runtimeConfig.browser"
  },
  "react-native": {
    "./dist-es/runtimeConfig": "./dist-es/runtimeConfig.native"
  },
  homepage: "https://github.com/aws/aws-sdk-js-v3/tree/main/clients/client-bedrock",
  repository: {
    type: "git",
    url: "https://github.com/aws/aws-sdk-js-v3.git",
    directory: "clients/client-bedrock"
  }
};

// node_modules/@aws-crypto/util/node_modules/@smithy/util-utf8/dist-es/fromUtf8.browser.js
var fromUtf82 = (input) => new TextEncoder().encode(input);

// node_modules/@aws-crypto/util/build/module/convertToBuffer.js
var fromUtf83 = typeof Buffer !== "undefined" && Buffer.from ? function(input) {
  return Buffer.from(input, "utf8");
} : fromUtf82;
function convertToBuffer(data) {
  if (data instanceof Uint8Array)
    return data;
  if (typeof data === "string") {
    return fromUtf83(data);
  }
  if (ArrayBuffer.isView(data)) {
    return new Uint8Array(data.buffer, data.byteOffset, data.byteLength / Uint8Array.BYTES_PER_ELEMENT);
  }
  return new Uint8Array(data);
}

// node_modules/@aws-crypto/util/build/module/isEmptyData.js
function isEmptyData(data) {
  if (typeof data === "string") {
    return data.length === 0;
  }
  return data.byteLength === 0;
}

// node_modules/@aws-crypto/sha256-browser/build/module/constants.js
var SHA_256_HASH = { name: "SHA-256" };
var SHA_256_HMAC_ALGO = {
  name: "HMAC",
  hash: SHA_256_HASH
};
var EMPTY_DATA_SHA_256 = new Uint8Array([
  227,
  176,
  196,
  66,
  152,
  252,
  28,
  20,
  154,
  251,
  244,
  200,
  153,
  111,
  185,
  36,
  39,
  174,
  65,
  228,
  100,
  155,
  147,
  76,
  164,
  149,
  153,
  27,
  120,
  82,
  184,
  85
]);

// node_modules/@aws-sdk/util-locate-window/dist-es/index.js
var fallbackWindow = {};
function locateWindow() {
  if (typeof window !== "undefined") {
    return window;
  } else if (typeof self !== "undefined") {
    return self;
  }
  return fallbackWindow;
}

// node_modules/@aws-crypto/sha256-browser/build/module/webCryptoSha256.js
var Sha256 = (
  /** @class */
  (function() {
    function Sha2564(secret) {
      this.toHash = new Uint8Array(0);
      this.secret = secret;
      this.reset();
    }
    Sha2564.prototype.update = function(data) {
      if (isEmptyData(data)) {
        return;
      }
      var update = convertToBuffer(data);
      var typedArray = new Uint8Array(this.toHash.byteLength + update.byteLength);
      typedArray.set(this.toHash, 0);
      typedArray.set(update, this.toHash.byteLength);
      this.toHash = typedArray;
    };
    Sha2564.prototype.digest = function() {
      var _this = this;
      if (this.key) {
        return this.key.then(function(key) {
          return locateWindow().crypto.subtle.sign(SHA_256_HMAC_ALGO, key, _this.toHash).then(function(data) {
            return new Uint8Array(data);
          });
        });
      }
      if (isEmptyData(this.toHash)) {
        return Promise.resolve(EMPTY_DATA_SHA_256);
      }
      return Promise.resolve().then(function() {
        return locateWindow().crypto.subtle.digest(SHA_256_HASH, _this.toHash);
      }).then(function(data) {
        return Promise.resolve(new Uint8Array(data));
      });
    };
    Sha2564.prototype.reset = function() {
      var _this = this;
      this.toHash = new Uint8Array(0);
      if (this.secret && this.secret !== void 0) {
        this.key = new Promise(function(resolve, reject) {
          locateWindow().crypto.subtle.importKey("raw", convertToBuffer(_this.secret), SHA_256_HMAC_ALGO, false, ["sign"]).then(resolve, reject);
        });
        this.key.catch(function() {
        });
      }
    };
    return Sha2564;
  })()
);

// node_modules/tslib/tslib.es6.mjs
function __awaiter(thisArg, _arguments, P, generator) {
  function adopt(value) {
    return value instanceof P ? value : new P(function(resolve) {
      resolve(value);
    });
  }
  return new (P || (P = Promise))(function(resolve, reject) {
    function fulfilled(value) {
      try {
        step(generator.next(value));
      } catch (e2) {
        reject(e2);
      }
    }
    function rejected(value) {
      try {
        step(generator["throw"](value));
      } catch (e2) {
        reject(e2);
      }
    }
    function step(result) {
      result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected);
    }
    step((generator = generator.apply(thisArg, _arguments || [])).next());
  });
}
function __generator(thisArg, body) {
  var _ = { label: 0, sent: function() {
    if (t2[0] & 1) throw t2[1];
    return t2[1];
  }, trys: [], ops: [] }, f2, y, t2, g2 = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
  return g2.next = verb(0), g2["throw"] = verb(1), g2["return"] = verb(2), typeof Symbol === "function" && (g2[Symbol.iterator] = function() {
    return this;
  }), g2;
  function verb(n2) {
    return function(v2) {
      return step([n2, v2]);
    };
  }
  function step(op) {
    if (f2) throw new TypeError("Generator is already executing.");
    while (g2 && (g2 = 0, op[0] && (_ = 0)), _) try {
      if (f2 = 1, y && (t2 = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t2 = y["return"]) && t2.call(y), 0) : y.next) && !(t2 = t2.call(y, op[1])).done) return t2;
      if (y = 0, t2) op = [op[0] & 2, t2.value];
      switch (op[0]) {
        case 0:
        case 1:
          t2 = op;
          break;
        case 4:
          _.label++;
          return { value: op[1], done: false };
        case 5:
          _.label++;
          y = op[1];
          op = [0];
          continue;
        case 7:
          op = _.ops.pop();
          _.trys.pop();
          continue;
        default:
          if (!(t2 = _.trys, t2 = t2.length > 0 && t2[t2.length - 1]) && (op[0] === 6 || op[0] === 2)) {
            _ = 0;
            continue;
          }
          if (op[0] === 3 && (!t2 || op[1] > t2[0] && op[1] < t2[3])) {
            _.label = op[1];
            break;
          }
          if (op[0] === 6 && _.label < t2[1]) {
            _.label = t2[1];
            t2 = op;
            break;
          }
          if (t2 && _.label < t2[2]) {
            _.label = t2[2];
            _.ops.push(op);
            break;
          }
          if (t2[2]) _.ops.pop();
          _.trys.pop();
          continue;
      }
      op = body.call(thisArg, _);
    } catch (e2) {
      op = [6, e2];
      y = 0;
    } finally {
      f2 = t2 = 0;
    }
    if (op[0] & 5) throw op[1];
    return { value: op[0] ? op[1] : void 0, done: true };
  }
}

// node_modules/@aws-crypto/sha256-js/build/module/constants.js
var BLOCK_SIZE = 64;
var DIGEST_LENGTH = 32;
var KEY = new Uint32Array([
  1116352408,
  1899447441,
  3049323471,
  3921009573,
  961987163,
  1508970993,
  2453635748,
  2870763221,
  3624381080,
  310598401,
  607225278,
  1426881987,
  1925078388,
  2162078206,
  2614888103,
  3248222580,
  3835390401,
  4022224774,
  264347078,
  604807628,
  770255983,
  1249150122,
  1555081692,
  1996064986,
  2554220882,
  2821834349,
  2952996808,
  3210313671,
  3336571891,
  3584528711,
  113926993,
  338241895,
  666307205,
  773529912,
  1294757372,
  1396182291,
  1695183700,
  1986661051,
  2177026350,
  2456956037,
  2730485921,
  2820302411,
  3259730800,
  3345764771,
  3516065817,
  3600352804,
  4094571909,
  275423344,
  430227734,
  506948616,
  659060556,
  883997877,
  958139571,
  1322822218,
  1537002063,
  1747873779,
  1955562222,
  2024104815,
  2227730452,
  2361852424,
  2428436474,
  2756734187,
  3204031479,
  3329325298
]);
var INIT = [
  1779033703,
  3144134277,
  1013904242,
  2773480762,
  1359893119,
  2600822924,
  528734635,
  1541459225
];
var MAX_HASHABLE_LENGTH = Math.pow(2, 53) - 1;

// node_modules/@aws-crypto/sha256-js/build/module/RawSha256.js
var RawSha256 = (
  /** @class */
  (function() {
    function RawSha2562() {
      this.state = Int32Array.from(INIT);
      this.temp = new Int32Array(64);
      this.buffer = new Uint8Array(64);
      this.bufferLength = 0;
      this.bytesHashed = 0;
      this.finished = false;
    }
    RawSha2562.prototype.update = function(data) {
      if (this.finished) {
        throw new Error("Attempted to update an already finished hash.");
      }
      var position = 0;
      var byteLength = data.byteLength;
      this.bytesHashed += byteLength;
      if (this.bytesHashed * 8 > MAX_HASHABLE_LENGTH) {
        throw new Error("Cannot hash more than 2^53 - 1 bits");
      }
      while (byteLength > 0) {
        this.buffer[this.bufferLength++] = data[position++];
        byteLength--;
        if (this.bufferLength === BLOCK_SIZE) {
          this.hashBuffer();
          this.bufferLength = 0;
        }
      }
    };
    RawSha2562.prototype.digest = function() {
      if (!this.finished) {
        var bitsHashed = this.bytesHashed * 8;
        var bufferView = new DataView(this.buffer.buffer, this.buffer.byteOffset, this.buffer.byteLength);
        var undecoratedLength = this.bufferLength;
        bufferView.setUint8(this.bufferLength++, 128);
        if (undecoratedLength % BLOCK_SIZE >= BLOCK_SIZE - 8) {
          for (var i2 = this.bufferLength; i2 < BLOCK_SIZE; i2++) {
            bufferView.setUint8(i2, 0);
          }
          this.hashBuffer();
          this.bufferLength = 0;
        }
        for (var i2 = this.bufferLength; i2 < BLOCK_SIZE - 8; i2++) {
          bufferView.setUint8(i2, 0);
        }
        bufferView.setUint32(BLOCK_SIZE - 8, Math.floor(bitsHashed / 4294967296), true);
        bufferView.setUint32(BLOCK_SIZE - 4, bitsHashed);
        this.hashBuffer();
        this.finished = true;
      }
      var out = new Uint8Array(DIGEST_LENGTH);
      for (var i2 = 0; i2 < 8; i2++) {
        out[i2 * 4] = this.state[i2] >>> 24 & 255;
        out[i2 * 4 + 1] = this.state[i2] >>> 16 & 255;
        out[i2 * 4 + 2] = this.state[i2] >>> 8 & 255;
        out[i2 * 4 + 3] = this.state[i2] >>> 0 & 255;
      }
      return out;
    };
    RawSha2562.prototype.hashBuffer = function() {
      var _a2 = this, buffer = _a2.buffer, state = _a2.state;
      var state0 = state[0], state1 = state[1], state2 = state[2], state3 = state[3], state4 = state[4], state5 = state[5], state6 = state[6], state7 = state[7];
      for (var i2 = 0; i2 < BLOCK_SIZE; i2++) {
        if (i2 < 16) {
          this.temp[i2] = (buffer[i2 * 4] & 255) << 24 | (buffer[i2 * 4 + 1] & 255) << 16 | (buffer[i2 * 4 + 2] & 255) << 8 | buffer[i2 * 4 + 3] & 255;
        } else {
          var u2 = this.temp[i2 - 2];
          var t1_1 = (u2 >>> 17 | u2 << 15) ^ (u2 >>> 19 | u2 << 13) ^ u2 >>> 10;
          u2 = this.temp[i2 - 15];
          var t2_1 = (u2 >>> 7 | u2 << 25) ^ (u2 >>> 18 | u2 << 14) ^ u2 >>> 3;
          this.temp[i2] = (t1_1 + this.temp[i2 - 7] | 0) + (t2_1 + this.temp[i2 - 16] | 0);
        }
        var t1 = (((state4 >>> 6 | state4 << 26) ^ (state4 >>> 11 | state4 << 21) ^ (state4 >>> 25 | state4 << 7)) + (state4 & state5 ^ ~state4 & state6) | 0) + (state7 + (KEY[i2] + this.temp[i2] | 0) | 0) | 0;
        var t2 = ((state0 >>> 2 | state0 << 30) ^ (state0 >>> 13 | state0 << 19) ^ (state0 >>> 22 | state0 << 10)) + (state0 & state1 ^ state0 & state2 ^ state1 & state2) | 0;
        state7 = state6;
        state6 = state5;
        state5 = state4;
        state4 = state3 + t1 | 0;
        state3 = state2;
        state2 = state1;
        state1 = state0;
        state0 = t1 + t2 | 0;
      }
      state[0] += state0;
      state[1] += state1;
      state[2] += state2;
      state[3] += state3;
      state[4] += state4;
      state[5] += state5;
      state[6] += state6;
      state[7] += state7;
    };
    return RawSha2562;
  })()
);

// node_modules/@aws-crypto/sha256-js/build/module/jsSha256.js
var Sha2562 = (
  /** @class */
  (function() {
    function Sha2564(secret) {
      this.secret = secret;
      this.hash = new RawSha256();
      this.reset();
    }
    Sha2564.prototype.update = function(toHash) {
      if (isEmptyData(toHash) || this.error) {
        return;
      }
      try {
        this.hash.update(convertToBuffer(toHash));
      } catch (e2) {
        this.error = e2;
      }
    };
    Sha2564.prototype.digestSync = function() {
      if (this.error) {
        throw this.error;
      }
      if (this.outer) {
        if (!this.outer.finished) {
          this.outer.update(this.hash.digest());
        }
        return this.outer.digest();
      }
      return this.hash.digest();
    };
    Sha2564.prototype.digest = function() {
      return __awaiter(this, void 0, void 0, function() {
        return __generator(this, function(_a2) {
          return [2, this.digestSync()];
        });
      });
    };
    Sha2564.prototype.reset = function() {
      this.hash = new RawSha256();
      if (this.secret) {
        this.outer = new RawSha256();
        var inner = bufferFromSecret(this.secret);
        var outer = new Uint8Array(BLOCK_SIZE);
        outer.set(inner);
        for (var i2 = 0; i2 < BLOCK_SIZE; i2++) {
          inner[i2] ^= 54;
          outer[i2] ^= 92;
        }
        this.hash.update(inner);
        this.outer.update(outer);
        for (var i2 = 0; i2 < inner.byteLength; i2++) {
          inner[i2] = 0;
        }
      }
    };
    return Sha2564;
  })()
);
function bufferFromSecret(secret) {
  var input = convertToBuffer(secret);
  if (input.byteLength > BLOCK_SIZE) {
    var bufferHash = new RawSha256();
    bufferHash.update(input);
    input = bufferHash.digest();
  }
  var buffer = new Uint8Array(BLOCK_SIZE);
  buffer.set(input);
  return buffer;
}

// node_modules/@aws-crypto/supports-web-crypto/build/module/supportsWebCrypto.js
var subtleCryptoMethods = [
  "decrypt",
  "digest",
  "encrypt",
  "exportKey",
  "generateKey",
  "importKey",
  "sign",
  "verify"
];
function supportsWebCrypto(window2) {
  if (supportsSecureRandom(window2) && typeof window2.crypto.subtle === "object") {
    var subtle = window2.crypto.subtle;
    return supportsSubtleCrypto(subtle);
  }
  return false;
}
function supportsSecureRandom(window2) {
  if (typeof window2 === "object" && typeof window2.crypto === "object") {
    var getRandomValues = window2.crypto.getRandomValues;
    return typeof getRandomValues === "function";
  }
  return false;
}
function supportsSubtleCrypto(subtle) {
  return subtle && subtleCryptoMethods.every(function(methodName) {
    return typeof subtle[methodName] === "function";
  });
}

// node_modules/@aws-crypto/sha256-browser/build/module/crossPlatformSha256.js
var Sha2563 = (
  /** @class */
  (function() {
    function Sha2564(secret) {
      if (supportsWebCrypto(locateWindow())) {
        this.hash = new Sha256(secret);
      } else {
        this.hash = new Sha2562(secret);
      }
    }
    Sha2564.prototype.update = function(data, encoding) {
      this.hash.update(convertToBuffer(data));
    };
    Sha2564.prototype.digest = function() {
      return this.hash.digest();
    };
    Sha2564.prototype.reset = function() {
      this.hash.reset();
    };
    return Sha2564;
  })()
);

// node_modules/@aws-sdk/util-user-agent-browser/dist-es/index.js
var createDefaultUserAgentProvider = ({ serviceId, clientVersion }) => async (config) => {
  const navigator = typeof window !== "undefined" ? window.navigator : void 0;
  const uaString = navigator?.userAgent ?? "";
  const osName = navigator?.userAgentData?.platform ?? fallback.os(uaString) ?? "other";
  const osVersion = void 0;
  const brands = navigator?.userAgentData?.brands ?? [];
  const brand = brands[brands.length - 1];
  const browserName = brand?.brand ?? fallback.browser(uaString) ?? "unknown";
  const browserVersion = brand?.version ?? "unknown";
  const sections = [
    ["aws-sdk-js", clientVersion],
    ["ua", "2.1"],
    [`os/${osName}`, osVersion],
    ["lang/js"],
    ["md/browser", `${browserName}_${browserVersion}`]
  ];
  if (serviceId) {
    sections.push([`api/${serviceId}`, clientVersion]);
  }
  const appId = await config?.userAgentAppId?.();
  if (appId) {
    sections.push([`app/${appId}`]);
  }
  return sections;
};
var fallback = {
  os(ua) {
    if (/iPhone|iPad|iPod/.test(ua))
      return "iOS";
    if (/Macintosh|Mac OS X/.test(ua))
      return "macOS";
    if (/Windows NT/.test(ua))
      return "Windows";
    if (/Android/.test(ua))
      return "Android";
    if (/Linux/.test(ua))
      return "Linux";
    return void 0;
  },
  browser(ua) {
    if (/EdgiOS|EdgA|Edg\//.test(ua))
      return "Microsoft Edge";
    if (/Firefox\//.test(ua))
      return "Firefox";
    if (/Chrome\//.test(ua))
      return "Chrome";
    if (/Safari\//.test(ua))
      return "Safari";
    return void 0;
  }
};

// node_modules/@smithy/fetch-http-handler/dist-es/create-request.js
function createRequest(url, requestOptions) {
  return new Request(url, requestOptions);
}

// node_modules/@smithy/fetch-http-handler/dist-es/request-timeout.js
function requestTimeout(timeoutInMs = 0) {
  return new Promise((resolve, reject) => {
    if (timeoutInMs) {
      setTimeout(() => {
        const timeoutError = new Error(`Request did not complete within ${timeoutInMs} ms`);
        timeoutError.name = "TimeoutError";
        reject(timeoutError);
      }, timeoutInMs);
    }
  });
}

// node_modules/@smithy/fetch-http-handler/dist-es/fetch-http-handler.js
var keepAliveSupport = {
  supported: void 0
};
var FetchHttpHandler = class _FetchHttpHandler {
  config;
  configProvider;
  static create(instanceOrOptions) {
    if (typeof instanceOrOptions?.handle === "function") {
      return instanceOrOptions;
    }
    return new _FetchHttpHandler(instanceOrOptions);
  }
  constructor(options) {
    if (typeof options === "function") {
      this.configProvider = options().then((opts) => opts || {});
    } else {
      this.config = options ?? {};
      this.configProvider = Promise.resolve(this.config);
    }
    if (keepAliveSupport.supported === void 0) {
      keepAliveSupport.supported = Boolean(typeof Request !== "undefined" && "keepalive" in createRequest("https://[::1]"));
    }
  }
  destroy() {
  }
  async handle(request, { abortSignal, requestTimeout: requestTimeout2 } = {}) {
    if (!this.config) {
      this.config = await this.configProvider;
    }
    const requestTimeoutInMs = requestTimeout2 ?? this.config.requestTimeout;
    const keepAlive = this.config.keepAlive === true;
    const credentials = this.config.credentials;
    if (abortSignal?.aborted) {
      const abortError = buildAbortError(abortSignal);
      return Promise.reject(abortError);
    }
    let path = request.path;
    const queryString = buildQueryString(request.query || {});
    if (queryString) {
      path += `?${queryString}`;
    }
    if (request.fragment) {
      path += `#${request.fragment}`;
    }
    let auth = "";
    if (request.username != null || request.password != null) {
      const username = request.username ?? "";
      const password = request.password ?? "";
      auth = `${username}:${password}@`;
    }
    const { port, method } = request;
    const url = `${request.protocol}//${auth}${request.hostname}${port ? `:${port}` : ""}${path}`;
    const body = method === "GET" || method === "HEAD" ? void 0 : request.body;
    const requestOptions = {
      body,
      headers: new Headers(request.headers),
      method,
      credentials
    };
    if (this.config?.cache) {
      requestOptions.cache = this.config.cache;
    }
    if (body) {
      requestOptions.duplex = "half";
    }
    if (typeof AbortController !== "undefined") {
      requestOptions.signal = abortSignal;
    }
    if (keepAliveSupport.supported) {
      requestOptions.keepalive = keepAlive;
    }
    if (typeof this.config.requestInit === "function") {
      Object.assign(requestOptions, this.config.requestInit(request));
    }
    let removeSignalEventListener = () => {
    };
    const fetchRequest = createRequest(url, requestOptions);
    const raceOfPromises = [
      fetch(fetchRequest).then((response) => {
        const fetchHeaders = response.headers;
        const transformedHeaders = {};
        for (const pair of fetchHeaders.entries()) {
          transformedHeaders[pair[0]] = pair[1];
        }
        const hasReadableStream = response.body != void 0;
        if (!hasReadableStream) {
          return response.blob().then((body2) => ({
            response: new HttpResponse({
              headers: transformedHeaders,
              reason: response.statusText,
              statusCode: response.status,
              body: body2
            })
          }));
        }
        return {
          response: new HttpResponse({
            headers: transformedHeaders,
            reason: response.statusText,
            statusCode: response.status,
            body: response.body
          })
        };
      }),
      requestTimeout(requestTimeoutInMs)
    ];
    if (abortSignal) {
      raceOfPromises.push(new Promise((resolve, reject) => {
        const onAbort = () => {
          const abortError = buildAbortError(abortSignal);
          reject(abortError);
        };
        if (typeof abortSignal.addEventListener === "function") {
          const signal = abortSignal;
          signal.addEventListener("abort", onAbort, { once: true });
          removeSignalEventListener = () => signal.removeEventListener("abort", onAbort);
        } else {
          abortSignal.onabort = onAbort;
        }
      }));
    }
    return Promise.race(raceOfPromises).finally(removeSignalEventListener);
  }
  updateHttpClientConfig(key, value) {
    this.config = void 0;
    this.configProvider = this.configProvider.then((config) => {
      config[key] = value;
      return config;
    });
  }
  httpHandlerConfigs() {
    return this.config ?? {};
  }
};
function buildAbortError(abortSignal) {
  const reason = abortSignal && typeof abortSignal === "object" && "reason" in abortSignal ? abortSignal.reason : void 0;
  if (reason) {
    if (reason instanceof Error) {
      const abortError3 = new Error("Request aborted");
      abortError3.name = "AbortError";
      abortError3.cause = reason;
      return abortError3;
    }
    const abortError2 = new Error(String(reason));
    abortError2.name = "AbortError";
    return abortError2;
  }
  const abortError = new Error("Request aborted");
  abortError.name = "AbortError";
  return abortError;
}

// node_modules/@smithy/fetch-http-handler/dist-es/index.js
init_index_browser2();

// node_modules/@smithy/util-body-length-browser/dist-es/index.js
init_index_browser2();

// node_modules/@aws-sdk/client-bedrock/dist-es/endpoint/ruleset.js
var s = "required";
var t = "fn";
var u = "argv";
var v = "ref";
var a = true;
var b = "isSet";
var c = "booleanEquals";
var d = "error";
var e = "endpoint";
var f = "tree";
var g = "PartitionResult";
var h = { [s]: false, "type": "string" };
var i = { [s]: true, "default": false, "type": "boolean" };
var j = { [v]: "Endpoint" };
var k = { [t]: c, [u]: [{ [v]: "UseFIPS" }, true] };
var l = { [t]: c, [u]: [{ [v]: "UseDualStack" }, true] };
var m = {};
var n = { [t]: "getAttr", [u]: [{ [v]: g }, "supportsFIPS"] };
var o = { [t]: c, [u]: [true, { [t]: "getAttr", [u]: [{ [v]: g }, "supportsDualStack"] }] };
var p = [k];
var q = [l];
var r = [{ [v]: "Region" }];
var _data = { version: "1.0", parameters: { Region: h, UseDualStack: i, UseFIPS: i, Endpoint: h }, rules: [{ conditions: [{ [t]: b, [u]: [j] }], rules: [{ conditions: p, error: "Invalid Configuration: FIPS and custom endpoint are not supported", type: d }, { rules: [{ conditions: q, error: "Invalid Configuration: Dualstack and custom endpoint are not supported", type: d }, { endpoint: { url: j, properties: m, headers: m }, type: e }], type: f }], type: f }, { rules: [{ conditions: [{ [t]: b, [u]: r }], rules: [{ conditions: [{ [t]: "aws.partition", [u]: r, assign: g }], rules: [{ conditions: [k, l], rules: [{ conditions: [{ [t]: c, [u]: [a, n] }, o], rules: [{ rules: [{ endpoint: { url: "https://bedrock-fips.{Region}.{PartitionResult#dualStackDnsSuffix}", properties: m, headers: m }, type: e }], type: f }], type: f }, { error: "FIPS and DualStack are enabled, but this partition does not support one or both", type: d }], type: f }, { conditions: p, rules: [{ conditions: [{ [t]: c, [u]: [n, a] }], rules: [{ rules: [{ endpoint: { url: "https://bedrock-fips.{Region}.{PartitionResult#dnsSuffix}", properties: m, headers: m }, type: e }], type: f }], type: f }, { error: "FIPS is enabled but this partition does not support FIPS", type: d }], type: f }, { conditions: q, rules: [{ conditions: [o], rules: [{ rules: [{ endpoint: { url: "https://bedrock.{Region}.{PartitionResult#dualStackDnsSuffix}", properties: m, headers: m }, type: e }], type: f }], type: f }, { error: "DualStack is enabled but this partition does not support DualStack", type: d }], type: f }, { rules: [{ endpoint: { url: "https://bedrock.{Region}.{PartitionResult#dnsSuffix}", properties: m, headers: m }, type: e }], type: f }], type: f }], type: f }, { error: "Invalid Configuration: Missing Region", type: d }], type: f }] };
var ruleSet = _data;

// node_modules/@aws-sdk/client-bedrock/dist-es/endpoint/endpointResolver.js
var cache = new EndpointCache({
  size: 50,
  params: ["Endpoint", "Region", "UseDualStack", "UseFIPS"]
});
var defaultEndpointResolver = (endpointParams, context = {}) => {
  return cache.get(endpointParams, () => resolveEndpoint(ruleSet, {
    endpointParams,
    logger: context.logger
  }));
};
customEndpointFunctions.aws = awsEndpointFunctions;

// node_modules/@aws-sdk/client-bedrock/dist-es/runtimeConfig.shared.js
var getRuntimeConfig = (config) => {
  return {
    apiVersion: "2023-04-20",
    base64Decoder: config?.base64Decoder ?? fromBase64,
    base64Encoder: config?.base64Encoder ?? toBase64,
    disableHostPrefix: config?.disableHostPrefix ?? false,
    endpointProvider: config?.endpointProvider ?? defaultEndpointResolver,
    extensions: config?.extensions ?? [],
    httpAuthSchemeProvider: config?.httpAuthSchemeProvider ?? defaultBedrockHttpAuthSchemeProvider,
    httpAuthSchemes: config?.httpAuthSchemes ?? [
      {
        schemeId: "aws.auth#sigv4",
        identityProvider: (ipc) => ipc.getIdentityProvider("aws.auth#sigv4"),
        signer: new AwsSdkSigV4Signer()
      },
      {
        schemeId: "smithy.api#httpBearerAuth",
        identityProvider: (ipc) => ipc.getIdentityProvider("smithy.api#httpBearerAuth"),
        signer: new HttpBearerAuthSigner()
      }
    ],
    logger: config?.logger ?? new NoOpLogger(),
    protocol: config?.protocol ?? AwsRestJsonProtocol,
    protocolSettings: config?.protocolSettings ?? {
      defaultNamespace: "com.amazonaws.bedrock",
      version: "2023-04-20",
      serviceTarget: "AmazonBedrockControlPlaneService"
    },
    serviceId: config?.serviceId ?? "Bedrock",
    urlParser: config?.urlParser ?? parseUrl,
    utf8Decoder: config?.utf8Decoder ?? fromUtf8,
    utf8Encoder: config?.utf8Encoder ?? toUtf8
  };
};

// node_modules/@aws-sdk/client-bedrock/dist-es/runtimeConfig.browser.js
var getRuntimeConfig2 = (config) => {
  const defaultsMode = resolveDefaultsModeConfig(config);
  const defaultConfigProvider = () => defaultsMode().then(loadConfigsForDefaultMode);
  const clientSharedValues = getRuntimeConfig(config);
  return {
    ...clientSharedValues,
    ...config,
    runtime: "browser",
    defaultsMode,
    bodyLengthChecker: config?.bodyLengthChecker ?? calculateBodyLength,
    credentialDefaultProvider: config?.credentialDefaultProvider ?? ((_) => () => Promise.reject(new Error("Credential is missing"))),
    defaultUserAgentProvider: config?.defaultUserAgentProvider ?? createDefaultUserAgentProvider({ serviceId: clientSharedValues.serviceId, clientVersion: package_default.version }),
    maxAttempts: config?.maxAttempts ?? DEFAULT_MAX_ATTEMPTS,
    region: config?.region ?? invalidProvider("Region is missing"),
    requestHandler: FetchHttpHandler.create(config?.requestHandler ?? defaultConfigProvider),
    retryMode: config?.retryMode ?? (async () => (await defaultConfigProvider()).retryMode || DEFAULT_RETRY_MODE),
    sha256: config?.sha256 ?? Sha2563,
    streamCollector: config?.streamCollector ?? streamCollector,
    useDualstackEndpoint: config?.useDualstackEndpoint ?? (() => Promise.resolve(DEFAULT_USE_DUALSTACK_ENDPOINT)),
    useFipsEndpoint: config?.useFipsEndpoint ?? (() => Promise.resolve(DEFAULT_USE_FIPS_ENDPOINT))
  };
};

// node_modules/@aws-sdk/region-config-resolver/dist-es/extensions/index.js
var getAwsRegionExtensionConfiguration = (runtimeConfig) => {
  return {
    setRegion(region) {
      runtimeConfig.region = region;
    },
    region() {
      return runtimeConfig.region;
    }
  };
};
var resolveAwsRegionExtensionConfiguration = (awsRegionExtensionConfiguration) => {
  return {
    region: awsRegionExtensionConfiguration.region()
  };
};

// node_modules/@aws-sdk/client-bedrock/dist-es/auth/httpAuthExtensionConfiguration.js
var getHttpAuthExtensionConfiguration = (runtimeConfig) => {
  const _httpAuthSchemes = runtimeConfig.httpAuthSchemes;
  let _httpAuthSchemeProvider = runtimeConfig.httpAuthSchemeProvider;
  let _credentials = runtimeConfig.credentials;
  let _token = runtimeConfig.token;
  return {
    setHttpAuthScheme(httpAuthScheme) {
      const index = _httpAuthSchemes.findIndex((scheme) => scheme.schemeId === httpAuthScheme.schemeId);
      if (index === -1) {
        _httpAuthSchemes.push(httpAuthScheme);
      } else {
        _httpAuthSchemes.splice(index, 1, httpAuthScheme);
      }
    },
    httpAuthSchemes() {
      return _httpAuthSchemes;
    },
    setHttpAuthSchemeProvider(httpAuthSchemeProvider) {
      _httpAuthSchemeProvider = httpAuthSchemeProvider;
    },
    httpAuthSchemeProvider() {
      return _httpAuthSchemeProvider;
    },
    setCredentials(credentials) {
      _credentials = credentials;
    },
    credentials() {
      return _credentials;
    },
    setToken(token) {
      _token = token;
    },
    token() {
      return _token;
    }
  };
};
var resolveHttpAuthRuntimeConfig = (config) => {
  return {
    httpAuthSchemes: config.httpAuthSchemes(),
    httpAuthSchemeProvider: config.httpAuthSchemeProvider(),
    credentials: config.credentials(),
    token: config.token()
  };
};

// node_modules/@aws-sdk/client-bedrock/dist-es/runtimeExtensions.js
var resolveRuntimeExtensions = (runtimeConfig, extensions) => {
  const extensionConfiguration = Object.assign(getAwsRegionExtensionConfiguration(runtimeConfig), getDefaultExtensionConfiguration(runtimeConfig), getHttpHandlerExtensionConfiguration(runtimeConfig), getHttpAuthExtensionConfiguration(runtimeConfig));
  extensions.forEach((extension) => extension.configure(extensionConfiguration));
  return Object.assign(runtimeConfig, resolveAwsRegionExtensionConfiguration(extensionConfiguration), resolveDefaultRuntimeConfig2(extensionConfiguration), resolveHttpHandlerRuntimeConfig(extensionConfiguration), resolveHttpAuthRuntimeConfig(extensionConfiguration));
};

// node_modules/@aws-sdk/client-bedrock/dist-es/BedrockClient.js
var BedrockClient = class extends Client {
  config;
  constructor(...[configuration]) {
    const _config_0 = getRuntimeConfig2(configuration || {});
    super(_config_0);
    this.initConfig = _config_0;
    const _config_1 = resolveClientEndpointParameters(_config_0);
    const _config_2 = resolveUserAgentConfig(_config_1);
    const _config_3 = resolveRetryConfig(_config_2);
    const _config_4 = resolveRegionConfig(_config_3);
    const _config_5 = resolveHostHeaderConfig(_config_4);
    const _config_6 = resolveEndpointConfig(_config_5);
    const _config_7 = resolveHttpAuthSchemeConfig(_config_6);
    const _config_8 = resolveRuntimeExtensions(_config_7, configuration?.extensions || []);
    this.config = _config_8;
    this.middlewareStack.use(getSchemaSerdePlugin(this.config));
    this.middlewareStack.use(getUserAgentPlugin(this.config));
    this.middlewareStack.use(getRetryPlugin(this.config));
    this.middlewareStack.use(getContentLengthPlugin(this.config));
    this.middlewareStack.use(getHostHeaderPlugin(this.config));
    this.middlewareStack.use(getLoggerPlugin(this.config));
    this.middlewareStack.use(getRecursionDetectionPlugin(this.config));
    this.middlewareStack.use(getHttpAuthSchemeEndpointRuleSetPlugin(this.config, {
      httpAuthSchemeParametersProvider: defaultBedrockHttpAuthSchemeParametersProvider,
      identityProviderConfigProvider: async (config) => new DefaultIdentityProviderConfig({
        "aws.auth#sigv4": config.credentials,
        "smithy.api#httpBearerAuth": config.token
      })
    }));
    this.middlewareStack.use(getHttpSigningPlugin(this.config));
  }
  destroy() {
    super.destroy();
  }
};

// node_modules/@aws-sdk/client-bedrock/dist-es/models/BedrockServiceException.js
var BedrockServiceException = class _BedrockServiceException extends ServiceException {
  constructor(options) {
    super(options);
    Object.setPrototypeOf(this, _BedrockServiceException.prototype);
  }
};

// node_modules/@aws-sdk/client-bedrock/dist-es/models/errors.js
var AccessDeniedException = class _AccessDeniedException extends BedrockServiceException {
  name = "AccessDeniedException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "AccessDeniedException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _AccessDeniedException.prototype);
  }
};
var InternalServerException = class _InternalServerException extends BedrockServiceException {
  name = "InternalServerException";
  $fault = "server";
  constructor(opts) {
    super({
      name: "InternalServerException",
      $fault: "server",
      ...opts
    });
    Object.setPrototypeOf(this, _InternalServerException.prototype);
  }
};
var ResourceNotFoundException = class _ResourceNotFoundException extends BedrockServiceException {
  name = "ResourceNotFoundException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "ResourceNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ResourceNotFoundException.prototype);
  }
};
var ThrottlingException = class _ThrottlingException extends BedrockServiceException {
  name = "ThrottlingException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "ThrottlingException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ThrottlingException.prototype);
  }
};
var ValidationException = class _ValidationException extends BedrockServiceException {
  name = "ValidationException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "ValidationException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ValidationException.prototype);
  }
};
var ConflictException = class _ConflictException extends BedrockServiceException {
  name = "ConflictException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "ConflictException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ConflictException.prototype);
  }
};
var ServiceQuotaExceededException = class _ServiceQuotaExceededException extends BedrockServiceException {
  name = "ServiceQuotaExceededException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "ServiceQuotaExceededException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ServiceQuotaExceededException.prototype);
  }
};
var TooManyTagsException = class _TooManyTagsException extends BedrockServiceException {
  name = "TooManyTagsException";
  $fault = "client";
  resourceName;
  constructor(opts) {
    super({
      name: "TooManyTagsException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TooManyTagsException.prototype);
    this.resourceName = opts.resourceName;
  }
};
var ResourceInUseException = class _ResourceInUseException extends BedrockServiceException {
  name = "ResourceInUseException";
  $fault = "client";
  constructor(opts) {
    super({
      name: "ResourceInUseException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ResourceInUseException.prototype);
  }
};
var ServiceUnavailableException = class _ServiceUnavailableException extends BedrockServiceException {
  name = "ServiceUnavailableException";
  $fault = "server";
  constructor(opts) {
    super({
      name: "ServiceUnavailableException",
      $fault: "server",
      ...opts
    });
    Object.setPrototypeOf(this, _ServiceUnavailableException.prototype);
  }
};

// node_modules/@aws-sdk/client-bedrock/dist-es/schemas/schemas_0.js
var _AA = "AgreementAvailability";
var _ADE = "AccessDeniedException";
var _AEC = "AutomatedEvaluationConfig";
var _AECM = "AutomatedEvaluationCustomMetrics";
var _AECMC = "AutomatedEvaluationCustomMetricConfig";
var _AECMS = "AutomatedEvaluationCustomMetricSource";
var _AEGIIC = "AccountEnforcedGuardrailInferenceInputConfiguration";
var _AEGOC = "AccountEnforcedGuardrailOutputConfiguration";
var _AEGOCc = "AccountEnforcedGuardrailsOutputConfiguration";
var _ARCDSL = "AutomatedReasoningCheckDifferenceScenarioList";
var _ARCF = "AutomatedReasoningCheckFinding";
var _ARCFL = "AutomatedReasoningCheckFindingList";
var _ARCIF = "AutomatedReasoningCheckImpossibleFinding";
var _ARCIFu = "AutomatedReasoningCheckInvalidFinding";
var _ARCITR = "AutomatedReasoningCheckInputTextReference";
var _ARCITRL = "AutomatedReasoningCheckInputTextReferenceList";
var _ARCLW = "AutomatedReasoningCheckLogicWarning";
var _ARCNTF = "AutomatedReasoningCheckNoTranslationsFinding";
var _ARCR = "AutomatedReasoningCheckRule";
var _ARCRL = "AutomatedReasoningCheckRuleList";
var _ARCS = "AutomatedReasoningCheckScenario";
var _ARCSF = "AutomatedReasoningCheckSatisfiableFinding";
var _ARCT = "AutomatedReasoningCheckTranslation";
var _ARCTAF = "AutomatedReasoningCheckTranslationAmbiguousFinding";
var _ARCTCF = "AutomatedReasoningCheckTooComplexFinding";
var _ARCTL = "AutomatedReasoningCheckTranslationList";
var _ARCTO = "AutomatedReasoningCheckTranslationOption";
var _ARCTOL = "AutomatedReasoningCheckTranslationOptionList";
var _ARCVF = "AutomatedReasoningCheckValidFinding";
var _ARLS = "AutomatedReasoningLogicStatement";
var _ARLSC = "AutomatedReasoningLogicStatementContent";
var _ARLSL = "AutomatedReasoningLogicStatementList";
var _ARNLSC = "AutomatedReasoningNaturalLanguageStatementContent";
var _ARPA = "AutomatedReasoningPolicyAnnotation";
var _ARPAFNL = "AutomatedReasoningPolicyAnnotationFeedbackNaturalLanguage";
var _ARPAIC = "AutomatedReasoningPolicyAnnotationIngestContent";
var _ARPAL = "AutomatedReasoningPolicyAnnotationList";
var _ARPARA = "AutomatedReasoningPolicyAddRuleAnnotation";
var _ARPARFNLA = "AutomatedReasoningPolicyAddRuleFromNaturalLanguageAnnotation";
var _ARPARM = "AutomatedReasoningPolicyAddRuleMutation";
var _ARPARNL = "AutomatedReasoningPolicyAnnotationRuleNaturalLanguage";
var _ARPATA = "AutomatedReasoningPolicyAddTypeAnnotation";
var _ARPATM = "AutomatedReasoningPolicyAddTypeMutation";
var _ARPATV = "AutomatedReasoningPolicyAddTypeValue";
var _ARPAVA = "AutomatedReasoningPolicyAddVariableAnnotation";
var _ARPAVM = "AutomatedReasoningPolicyAddVariableMutation";
var _ARPBDB = "AutomatedReasoningPolicyBuildDocumentBlob";
var _ARPBDD = "AutomatedReasoningPolicyBuildDocumentDescription";
var _ARPBDN = "AutomatedReasoningPolicyBuildDocumentName";
var _ARPBL = "AutomatedReasoningPolicyBuildLog";
var _ARPBLE = "AutomatedReasoningPolicyBuildLogEntry";
var _ARPBLEL = "AutomatedReasoningPolicyBuildLogEntryList";
var _ARPBRA = "AutomatedReasoningPolicyBuildResultAssets";
var _ARPBS = "AutomatedReasoningPolicyBuildStep";
var _ARPBSC = "AutomatedReasoningPolicyBuildStepContext";
var _ARPBSL = "AutomatedReasoningPolicyBuildStepList";
var _ARPBSM = "AutomatedReasoningPolicyBuildStepMessage";
var _ARPBSML = "AutomatedReasoningPolicyBuildStepMessageList";
var _ARPBWD = "AutomatedReasoningPolicyBuildWorkflowDocument";
var _ARPBWDL = "AutomatedReasoningPolicyBuildWorkflowDocumentList";
var _ARPBWRC = "AutomatedReasoningPolicyBuildWorkflowRepairContent";
var _ARPBWS = "AutomatedReasoningPolicyBuildWorkflowSource";
var _ARPBWSu = "AutomatedReasoningPolicyBuildWorkflowSummary";
var _ARPBWSut = "AutomatedReasoningPolicyBuildWorkflowSummaries";
var _ARPD = "AutomatedReasoningPolicyDescription";
var _ARPDE = "AutomatedReasoningPolicyDefinitionElement";
var _ARPDQR = "AutomatedReasoningPolicyDefinitionQualityReport";
var _ARPDR = "AutomatedReasoningPolicyDefinitionRule";
var _ARPDRA = "AutomatedReasoningPolicyDeleteRuleAnnotation";
var _ARPDRAE = "AutomatedReasoningPolicyDefinitionRuleAlternateExpression";
var _ARPDRE = "AutomatedReasoningPolicyDefinitionRuleExpression";
var _ARPDRL = "AutomatedReasoningPolicyDefinitionRuleList";
var _ARPDRM = "AutomatedReasoningPolicyDeleteRuleMutation";
var _ARPDRS = "AutomatedReasoningPolicyDisjointRuleSet";
var _ARPDRSL = "AutomatedReasoningPolicyDisjointRuleSetList";
var _ARPDT = "AutomatedReasoningPolicyDefinitionType";
var _ARPDTA = "AutomatedReasoningPolicyDeleteTypeAnnotation";
var _ARPDTD = "AutomatedReasoningPolicyDefinitionTypeDescription";
var _ARPDTL = "AutomatedReasoningPolicyDefinitionTypeList";
var _ARPDTM = "AutomatedReasoningPolicyDeleteTypeMutation";
var _ARPDTN = "AutomatedReasoningPolicyDefinitionTypeName";
var _ARPDTNL = "AutomatedReasoningPolicyDefinitionTypeNameList";
var _ARPDTV = "AutomatedReasoningPolicyDefinitionTypeValue";
var _ARPDTVD = "AutomatedReasoningPolicyDefinitionTypeValueDescription";
var _ARPDTVL = "AutomatedReasoningPolicyDefinitionTypeValueList";
var _ARPDTVP = "AutomatedReasoningPolicyDefinitionTypeValuePair";
var _ARPDTVPL = "AutomatedReasoningPolicyDefinitionTypeValuePairList";
var _ARPDTVu = "AutomatedReasoningPolicyDeleteTypeValue";
var _ARPDV = "AutomatedReasoningPolicyDefinitionVariable";
var _ARPDVA = "AutomatedReasoningPolicyDeleteVariableAnnotation";
var _ARPDVD = "AutomatedReasoningPolicyDefinitionVariableDescription";
var _ARPDVL = "AutomatedReasoningPolicyDefinitionVariableList";
var _ARPDVM = "AutomatedReasoningPolicyDeleteVariableMutation";
var _ARPDVN = "AutomatedReasoningPolicyDefinitionVariableName";
var _ARPDVNL = "AutomatedReasoningPolicyDefinitionVariableNameList";
var _ARPDu = "AutomatedReasoningPolicyDefinition";
var _ARPGTC = "AutomatedReasoningPolicyGeneratedTestCase";
var _ARPGTCL = "AutomatedReasoningPolicyGeneratedTestCaseList";
var _ARPGTCu = "AutomatedReasoningPolicyGeneratedTestCases";
var _ARPICA = "AutomatedReasoningPolicyIngestContentAnnotation";
var _ARPM = "AutomatedReasoningPolicyMutation";
var _ARPN = "AutomatedReasoningPolicyName";
var _ARPP = "AutomatedReasoningPolicyPlanning";
var _ARPS = "AutomatedReasoningPolicyScenario";
var _ARPSAE = "AutomatedReasoningPolicyScenarioAlternateExpression";
var _ARPSE = "AutomatedReasoningPolicyScenarioExpression";
var _ARPSL = "AutomatedReasoningPolicyScenarioList";
var _ARPSu = "AutomatedReasoningPolicyScenarios";
var _ARPSut = "AutomatedReasoningPolicySummary";
var _ARPSuto = "AutomatedReasoningPolicySummaries";
var _ARPTC = "AutomatedReasoningPolicyTestCase";
var _ARPTCL = "AutomatedReasoningPolicyTestCaseList";
var _ARPTGC = "AutomatedReasoningPolicyTestGuardContent";
var _ARPTL = "AutomatedReasoningPolicyTestList";
var _ARPTQC = "AutomatedReasoningPolicyTestQueryContent";
var _ARPTR = "AutomatedReasoningPolicyTestResult";
var _ARPTVA = "AutomatedReasoningPolicyTypeValueAnnotation";
var _ARPTVAL = "AutomatedReasoningPolicyTypeValueAnnotationList";
var _ARPUFRFA = "AutomatedReasoningPolicyUpdateFromRuleFeedbackAnnotation";
var _ARPUFSFA = "AutomatedReasoningPolicyUpdateFromScenarioFeedbackAnnotation";
var _ARPURA = "AutomatedReasoningPolicyUpdateRuleAnnotation";
var _ARPURM = "AutomatedReasoningPolicyUpdateRuleMutation";
var _ARPUTA = "AutomatedReasoningPolicyUpdateTypeAnnotation";
var _ARPUTM = "AutomatedReasoningPolicyUpdateTypeMutation";
var _ARPUTV = "AutomatedReasoningPolicyUpdateTypeValue";
var _ARPUVA = "AutomatedReasoningPolicyUpdateVariableAnnotation";
var _ARPUVM = "AutomatedReasoningPolicyUpdateVariableMutation";
var _ARPWTC = "AutomatedReasoningPolicyWorkflowTypeContent";
var _BCB = "ByteContentBlob";
var _BCD = "ByteContentDoc";
var _BDEJ = "BatchDeleteEvaluationJob";
var _BDEJE = "BatchDeleteEvaluationJobError";
var _BDEJEa = "BatchDeleteEvaluationJobErrors";
var _BDEJI = "BatchDeleteEvaluationJobItem";
var _BDEJIa = "BatchDeleteEvaluationJobItems";
var _BDEJR = "BatchDeleteEvaluationJobRequest";
var _BDEJRa = "BatchDeleteEvaluationJobResponse";
var _BEM = "BedrockEvaluatorModel";
var _BEMe = "BedrockEvaluatorModels";
var _CARP = "CreateAutomatedReasoningPolicy";
var _CARPBW = "CancelAutomatedReasoningPolicyBuildWorkflow";
var _CARPBWR = "CancelAutomatedReasoningPolicyBuildWorkflowRequest";
var _CARPBWRa = "CancelAutomatedReasoningPolicyBuildWorkflowResponse";
var _CARPR = "CreateAutomatedReasoningPolicyRequest";
var _CARPRr = "CreateAutomatedReasoningPolicyResponse";
var _CARPTC = "CreateAutomatedReasoningPolicyTestCase";
var _CARPTCR = "CreateAutomatedReasoningPolicyTestCaseRequest";
var _CARPTCRr = "CreateAutomatedReasoningPolicyTestCaseResponse";
var _CARPV = "CreateAutomatedReasoningPolicyVersion";
var _CARPVR = "CreateAutomatedReasoningPolicyVersionRequest";
var _CARPVRr = "CreateAutomatedReasoningPolicyVersionResponse";
var _CC = "CustomizationConfig";
var _CCM = "CreateCustomModel";
var _CCMD = "CreateCustomModelDeployment";
var _CCMDR = "CreateCustomModelDeploymentRequest";
var _CCMDRr = "CreateCustomModelDeploymentResponse";
var _CCMR = "CreateCustomModelRequest";
var _CCMRr = "CreateCustomModelResponse";
var _CE = "ConflictException";
var _CEJ = "CreateEvaluationJob";
var _CEJR = "CreateEvaluationJobRequest";
var _CEJRr = "CreateEvaluationJobResponse";
var _CFMA = "CreateFoundationModelAgreement";
var _CFMAR = "CreateFoundationModelAgreementRequest";
var _CFMARr = "CreateFoundationModelAgreementResponse";
var _CG = "CreateGuardrail";
var _CGR = "CreateGuardrailRequest";
var _CGRr = "CreateGuardrailResponse";
var _CGV = "CreateGuardrailVersion";
var _CGVR = "CreateGuardrailVersionRequest";
var _CGVRr = "CreateGuardrailVersionResponse";
var _CIP = "CreateInferenceProfile";
var _CIPR = "CreateInferenceProfileRequest";
var _CIPRr = "CreateInferenceProfileResponse";
var _CMBEM = "CustomMetricBedrockEvaluatorModel";
var _CMBEMu = "CustomMetricBedrockEvaluatorModels";
var _CMCJ = "CreateModelCopyJob";
var _CMCJR = "CreateModelCopyJobRequest";
var _CMCJRr = "CreateModelCopyJobResponse";
var _CMCJRre = "CreateModelCustomizationJobRequest";
var _CMCJRrea = "CreateModelCustomizationJobResponse";
var _CMCJr = "CreateModelCustomizationJob";
var _CMD = "CustomMetricDefinition";
var _CMDS = "CustomModelDeploymentSummary";
var _CMDSL = "CustomModelDeploymentSummaryList";
var _CMDUD = "CustomModelDeploymentUpdateDetails";
var _CMEMC = "CustomMetricEvaluatorModelConfig";
var _CMIJ = "CreateModelImportJob";
var _CMIJR = "CreateModelImportJobRequest";
var _CMIJRr = "CreateModelImportJobResponse";
var _CMIJRre = "CreateModelInvocationJobRequest";
var _CMIJRrea = "CreateModelInvocationJobResponse";
var _CMIJr = "CreateModelInvocationJob";
var _CMME = "CreateMarketplaceModelEndpoint";
var _CMMER = "CreateMarketplaceModelEndpointRequest";
var _CMMERr = "CreateMarketplaceModelEndpointResponse";
var _CMS = "CustomModelSummary";
var _CMSL = "CustomModelSummaryList";
var _CMU = "CustomModelUnits";
var _CPMT = "CreateProvisionedModelThroughput";
var _CPMTR = "CreateProvisionedModelThroughputRequest";
var _CPMTRr = "CreateProvisionedModelThroughputResponse";
var _CPR = "CreatePromptRouter";
var _CPRR = "CreatePromptRouterRequest";
var _CPRRr = "CreatePromptRouterResponse";
var _CWC = "CloudWatchConfig";
var _DARP = "DeleteAutomatedReasoningPolicy";
var _DARPBW = "DeleteAutomatedReasoningPolicyBuildWorkflow";
var _DARPBWR = "DeleteAutomatedReasoningPolicyBuildWorkflowRequest";
var _DARPBWRe = "DeleteAutomatedReasoningPolicyBuildWorkflowResponse";
var _DARPR = "DeleteAutomatedReasoningPolicyRequest";
var _DARPRe = "DeleteAutomatedReasoningPolicyResponse";
var _DARPTC = "DeleteAutomatedReasoningPolicyTestCase";
var _DARPTCR = "DeleteAutomatedReasoningPolicyTestCaseRequest";
var _DARPTCRe = "DeleteAutomatedReasoningPolicyTestCaseResponse";
var _DC = "DistillationConfig";
var _DCM = "DeleteCustomModel";
var _DCMD = "DeleteCustomModelDeployment";
var _DCMDR = "DeleteCustomModelDeploymentRequest";
var _DCMDRe = "DeleteCustomModelDeploymentResponse";
var _DCMR = "DeleteCustomModelRequest";
var _DCMRe = "DeleteCustomModelResponse";
var _DEGC = "DeleteEnforcedGuardrailConfiguration";
var _DEGCR = "DeleteEnforcedGuardrailConfigurationRequest";
var _DEGCRe = "DeleteEnforcedGuardrailConfigurationResponse";
var _DFMA = "DeleteFoundationModelAgreement";
var _DFMAR = "DeleteFoundationModelAgreementRequest";
var _DFMARe = "DeleteFoundationModelAgreementResponse";
var _DG = "DeleteGuardrail";
var _DGR = "DeleteGuardrailRequest";
var _DGRe = "DeleteGuardrailResponse";
var _DIM = "DeleteImportedModel";
var _DIMR = "DeleteImportedModelRequest";
var _DIMRe = "DeleteImportedModelResponse";
var _DIP = "DeleteInferenceProfile";
var _DIPR = "DeleteInferenceProfileRequest";
var _DIPRe = "DeleteInferenceProfileResponse";
var _DMILC = "DeleteModelInvocationLoggingConfiguration";
var _DMILCR = "DeleteModelInvocationLoggingConfigurationRequest";
var _DMILCRe = "DeleteModelInvocationLoggingConfigurationResponse";
var _DMME = "DeleteMarketplaceModelEndpoint";
var _DMMER = "DeleteMarketplaceModelEndpointRequest";
var _DMMERe = "DeleteMarketplaceModelEndpointResponse";
var _DMMERer = "DeregisterMarketplaceModelEndpointRequest";
var _DMMERere = "DeregisterMarketplaceModelEndpointResponse";
var _DMMEe = "DeregisterMarketplaceModelEndpoint";
var _DPD = "DataProcessingDetails";
var _DPMT = "DeleteProvisionedModelThroughput";
var _DPMTR = "DeleteProvisionedModelThroughputRequest";
var _DPMTRe = "DeleteProvisionedModelThroughputResponse";
var _DPR = "DimensionalPriceRate";
var _DPRR = "DeletePromptRouterRequest";
var _DPRRe = "DeletePromptRouterResponse";
var _DPRe = "DeletePromptRouter";
var _EARPV = "ExportAutomatedReasoningPolicyVersion";
var _EARPVR = "ExportAutomatedReasoningPolicyVersionRequest";
var _EARPVRx = "ExportAutomatedReasoningPolicyVersionResponse";
var _EBM = "EvaluationBedrockModel";
var _EC = "EndpointConfig";
var _ECv = "EvaluationConfig";
var _ED = "EvaluationDataset";
var _EDL = "EvaluationDatasetLocation";
var _EDMC = "EvaluationDatasetMetricConfig";
var _EDMCv = "EvaluationDatasetMetricConfigs";
var _EDN = "EvaluationDatasetName";
var _EIC = "EvaluationInferenceConfig";
var _EICS = "EvaluationInferenceConfigSummary";
var _EJD = "EvaluationJobDescription";
var _EJI = "EvaluationJobIdentifier";
var _EJIv = "EvaluationJobIdentifiers";
var _EMC = "EvaluationModelConfigs";
var _EMCS = "EvaluationModelConfigSummary";
var _EMCv = "EvaluationModelConfig";
var _EMCva = "EvaluatorModelConfig";
var _EMD = "EvaluationMetricDescription";
var _EMIP = "EvaluationModelInferenceParams";
var _EMN = "EvaluationMetricName";
var _EMNv = "EvaluationMetricNames";
var _EODC = "EvaluationOutputDataConfig";
var _EPIS = "EvaluationPrecomputedInferenceSource";
var _EPRAGSC = "EvaluationPrecomputedRetrieveAndGenerateSourceConfig";
var _EPRSC = "EvaluationPrecomputedRetrieveSourceConfig";
var _EPRSCv = "EvaluationPrecomputedRagSourceConfig";
var _ERCS = "EvaluationRagConfigSummary";
var _ES = "EvaluationSummary";
var _ESGC = "ExternalSourcesGenerationConfiguration";
var _ESRAGC = "ExternalSourcesRetrieveAndGenerateConfiguration";
var _ESv = "EvaluationSummaries";
var _ESx = "ExternalSource";
var _ESxt = "ExternalSources";
var _FA = "FilterAttribute";
var _FFR = "FieldForReranking";
var _FFRi = "FieldsForReranking";
var _FMD = "FoundationModelDetails";
var _FML = "FoundationModelLifecycle";
var _FMS = "FoundationModelSummary";
var _FMSL = "FoundationModelSummaryList";
var _GARP = "GuardrailAutomatedReasoningPolicy";
var _GARPA = "GetAutomatedReasoningPolicyAnnotations";
var _GARPAR = "GetAutomatedReasoningPolicyAnnotationsRequest";
var _GARPARe = "GetAutomatedReasoningPolicyAnnotationsResponse";
var _GARPBW = "GetAutomatedReasoningPolicyBuildWorkflow";
var _GARPBWR = "GetAutomatedReasoningPolicyBuildWorkflowRequest";
var _GARPBWRA = "GetAutomatedReasoningPolicyBuildWorkflowResultAssets";
var _GARPBWRAR = "GetAutomatedReasoningPolicyBuildWorkflowResultAssetsRequest";
var _GARPBWRARe = "GetAutomatedReasoningPolicyBuildWorkflowResultAssetsResponse";
var _GARPBWRe = "GetAutomatedReasoningPolicyBuildWorkflowResponse";
var _GARPC = "GuardrailAutomatedReasoningPolicyConfig";
var _GARPNS = "GetAutomatedReasoningPolicyNextScenario";
var _GARPNSR = "GetAutomatedReasoningPolicyNextScenarioRequest";
var _GARPNSRe = "GetAutomatedReasoningPolicyNextScenarioResponse";
var _GARPR = "GetAutomatedReasoningPolicyRequest";
var _GARPRe = "GetAutomatedReasoningPolicyResponse";
var _GARPTC = "GetAutomatedReasoningPolicyTestCase";
var _GARPTCR = "GetAutomatedReasoningPolicyTestCaseRequest";
var _GARPTCRe = "GetAutomatedReasoningPolicyTestCaseResponse";
var _GARPTR = "GetAutomatedReasoningPolicyTestResult";
var _GARPTRR = "GetAutomatedReasoningPolicyTestResultRequest";
var _GARPTRRe = "GetAutomatedReasoningPolicyTestResultResponse";
var _GARPe = "GetAutomatedReasoningPolicy";
var _GBM = "GuardrailBlockedMessaging";
var _GC = "GenerationConfiguration";
var _GCF = "GuardrailContentFilter";
var _GCFA = "GuardrailContentFilterAction";
var _GCFC = "GuardrailContentFilterConfig";
var _GCFCu = "GuardrailContentFiltersConfig";
var _GCFT = "GuardrailContentFiltersTier";
var _GCFTC = "GuardrailContentFiltersTierConfig";
var _GCFTN = "GuardrailContentFiltersTierName";
var _GCFu = "GuardrailContentFilters";
var _GCGA = "GuardrailContextualGroundingAction";
var _GCGF = "GuardrailContextualGroundingFilter";
var _GCGFC = "GuardrailContextualGroundingFilterConfig";
var _GCGFCu = "GuardrailContextualGroundingFiltersConfig";
var _GCGFu = "GuardrailContextualGroundingFilters";
var _GCGP = "GuardrailContextualGroundingPolicy";
var _GCGPC = "GuardrailContextualGroundingPolicyConfig";
var _GCM = "GetCustomModel";
var _GCMD = "GetCustomModelDeployment";
var _GCMDR = "GetCustomModelDeploymentRequest";
var _GCMDRe = "GetCustomModelDeploymentResponse";
var _GCMR = "GetCustomModelRequest";
var _GCMRe = "GetCustomModelResponse";
var _GCP = "GuardrailContentPolicy";
var _GCPC = "GuardrailContentPolicyConfig";
var _GCRC = "GuardrailCrossRegionConfig";
var _GCRD = "GuardrailCrossRegionDetails";
var _GCr = "GraderConfig";
var _GCu = "GuardrailConfiguration";
var _GD = "GuardrailDescription";
var _GEJ = "GetEvaluationJob";
var _GEJR = "GetEvaluationJobRequest";
var _GEJRe = "GetEvaluationJobResponse";
var _GFM = "GetFoundationModel";
var _GFMA = "GetFoundationModelAvailability";
var _GFMAR = "GetFoundationModelAvailabilityRequest";
var _GFMARe = "GetFoundationModelAvailabilityResponse";
var _GFMR = "GetFoundationModelRequest";
var _GFMRe = "GetFoundationModelResponse";
var _GFR = "GuardrailFailureRecommendation";
var _GFRu = "GuardrailFailureRecommendations";
var _GG = "GetGuardrail";
var _GGR = "GetGuardrailRequest";
var _GGRe = "GetGuardrailResponse";
var _GIM = "GetImportedModel";
var _GIMR = "GetImportedModelRequest";
var _GIMRe = "GetImportedModelResponse";
var _GIP = "GetInferenceProfile";
var _GIPR = "GetInferenceProfileRequest";
var _GIPRe = "GetInferenceProfileResponse";
var _GM = "GuardrailModality";
var _GMCJ = "GetModelCopyJob";
var _GMCJR = "GetModelCopyJobRequest";
var _GMCJRe = "GetModelCopyJobResponse";
var _GMCJRet = "GetModelCustomizationJobRequest";
var _GMCJReto = "GetModelCustomizationJobResponse";
var _GMCJe = "GetModelCustomizationJob";
var _GMIJ = "GetModelImportJob";
var _GMIJR = "GetModelImportJobRequest";
var _GMIJRe = "GetModelImportJobResponse";
var _GMIJRet = "GetModelInvocationJobRequest";
var _GMIJReto = "GetModelInvocationJobResponse";
var _GMIJe = "GetModelInvocationJob";
var _GMILC = "GetModelInvocationLoggingConfiguration";
var _GMILCR = "GetModelInvocationLoggingConfigurationRequest";
var _GMILCRe = "GetModelInvocationLoggingConfigurationResponse";
var _GMME = "GetMarketplaceModelEndpoint";
var _GMMER = "GetMarketplaceModelEndpointRequest";
var _GMMERe = "GetMarketplaceModelEndpointResponse";
var _GMW = "GuardrailManagedWords";
var _GMWC = "GuardrailManagedWordsConfig";
var _GMWL = "GuardrailManagedWordLists";
var _GMWLC = "GuardrailManagedWordListsConfig";
var _GMu = "GuardrailModalities";
var _GN = "GuardrailName";
var _GPE = "GuardrailPiiEntity";
var _GPEC = "GuardrailPiiEntityConfig";
var _GPECu = "GuardrailPiiEntitiesConfig";
var _GPEu = "GuardrailPiiEntities";
var _GPMT = "GetProvisionedModelThroughput";
var _GPMTR = "GetProvisionedModelThroughputRequest";
var _GPMTRe = "GetProvisionedModelThroughputResponse";
var _GPR = "GetPromptRouter";
var _GPRR = "GetPromptRouterRequest";
var _GPRRe = "GetPromptRouterResponse";
var _GR = "GuardrailRegex";
var _GRC = "GuardrailRegexConfig";
var _GRCu = "GuardrailRegexesConfig";
var _GRu = "GuardrailRegexes";
var _GS = "GuardrailSummary";
var _GSIP = "GuardrailSensitiveInformationPolicy";
var _GSIPC = "GuardrailSensitiveInformationPolicyConfig";
var _GSR = "GuardrailStatusReason";
var _GSRu = "GuardrailStatusReasons";
var _GSu = "GuardrailSummaries";
var _GT = "GuardrailTopic";
var _GTA = "GuardrailTopicAction";
var _GTC = "GuardrailTopicConfig";
var _GTCu = "GuardrailTopicsConfig";
var _GTD = "GuardrailTopicDefinition";
var _GTE = "GuardrailTopicExample";
var _GTEu = "GuardrailTopicExamples";
var _GTN = "GuardrailTopicName";
var _GTP = "GuardrailTopicPolicy";
var _GTPC = "GuardrailTopicPolicyConfig";
var _GTT = "GuardrailTopicsTier";
var _GTTC = "GuardrailTopicsTierConfig";
var _GTTN = "GuardrailTopicsTierName";
var _GTu = "GuardrailTopics";
var _GUCFMA = "GetUseCaseForModelAccess";
var _GUCFMAR = "GetUseCaseForModelAccessRequest";
var _GUCFMARe = "GetUseCaseForModelAccessResponse";
var _GW = "GuardrailWord";
var _GWA = "GuardrailWordAction";
var _GWC = "GuardrailWordConfig";
var _GWCu = "GuardrailWordsConfig";
var _GWP = "GuardrailWordPolicy";
var _GWPC = "GuardrailWordPolicyConfig";
var _GWu = "GuardrailWords";
var _HEC = "HumanEvaluationConfig";
var _HECM = "HumanEvaluationCustomMetric";
var _HECMu = "HumanEvaluationCustomMetrics";
var _HTI = "HumanTaskInstructions";
var _HWC = "HumanWorkflowConfig";
var _I = "Identifier";
var _IFC = "ImplicitFilterConfiguration";
var _ILC = "InvocationLogsConfig";
var _ILS = "InvocationLogSource";
var _IMS = "ImportedModelSummary";
var _IMSL = "ImportedModelSummaryList";
var _IPD = "InferenceProfileDescription";
var _IPM = "InferenceProfileModel";
var _IPMS = "InferenceProfileModelSource";
var _IPMn = "InferenceProfileModels";
var _IPS = "InferenceProfileSummary";
var _IPSn = "InferenceProfileSummaries";
var _ISE = "InternalServerException";
var _KBC = "KnowledgeBaseConfig";
var _KBRAGC = "KnowledgeBaseRetrieveAndGenerateConfiguration";
var _KBRC = "KnowledgeBaseRetrievalConfiguration";
var _KBVSC = "KnowledgeBaseVectorSearchConfiguration";
var _KIC = "KbInferenceConfig";
var _LARP = "ListAutomatedReasoningPolicies";
var _LARPBW = "ListAutomatedReasoningPolicyBuildWorkflows";
var _LARPBWR = "ListAutomatedReasoningPolicyBuildWorkflowsRequest";
var _LARPBWRi = "ListAutomatedReasoningPolicyBuildWorkflowsResponse";
var _LARPR = "ListAutomatedReasoningPoliciesRequest";
var _LARPRi = "ListAutomatedReasoningPoliciesResponse";
var _LARPTC = "ListAutomatedReasoningPolicyTestCases";
var _LARPTCR = "ListAutomatedReasoningPolicyTestCasesRequest";
var _LARPTCRi = "ListAutomatedReasoningPolicyTestCasesResponse";
var _LARPTR = "ListAutomatedReasoningPolicyTestResults";
var _LARPTRR = "ListAutomatedReasoningPolicyTestResultsRequest";
var _LARPTRRi = "ListAutomatedReasoningPolicyTestResultsResponse";
var _LC = "LoggingConfig";
var _LCM = "ListCustomModels";
var _LCMD = "ListCustomModelDeployments";
var _LCMDR = "ListCustomModelDeploymentsRequest";
var _LCMDRi = "ListCustomModelDeploymentsResponse";
var _LCMR = "ListCustomModelsRequest";
var _LCMRi = "ListCustomModelsResponse";
var _LEGC = "ListEnforcedGuardrailsConfiguration";
var _LEGCR = "ListEnforcedGuardrailsConfigurationRequest";
var _LEGCRi = "ListEnforcedGuardrailsConfigurationResponse";
var _LEJ = "ListEvaluationJobs";
var _LEJR = "ListEvaluationJobsRequest";
var _LEJRi = "ListEvaluationJobsResponse";
var _LFM = "ListFoundationModels";
var _LFMAO = "ListFoundationModelAgreementOffers";
var _LFMAOR = "ListFoundationModelAgreementOffersRequest";
var _LFMAORi = "ListFoundationModelAgreementOffersResponse";
var _LFMR = "ListFoundationModelsRequest";
var _LFMRi = "ListFoundationModelsResponse";
var _LG = "ListGuardrails";
var _LGC = "LambdaGraderConfig";
var _LGR = "ListGuardrailsRequest";
var _LGRi = "ListGuardrailsResponse";
var _LIM = "ListImportedModels";
var _LIMR = "ListImportedModelsRequest";
var _LIMRi = "ListImportedModelsResponse";
var _LIP = "ListInferenceProfiles";
var _LIPR = "ListInferenceProfilesRequest";
var _LIPRi = "ListInferenceProfilesResponse";
var _LMCJ = "ListModelCopyJobs";
var _LMCJR = "ListModelCopyJobsRequest";
var _LMCJRi = "ListModelCopyJobsResponse";
var _LMCJRis = "ListModelCustomizationJobsRequest";
var _LMCJRist = "ListModelCustomizationJobsResponse";
var _LMCJi = "ListModelCustomizationJobs";
var _LMIJ = "ListModelImportJobs";
var _LMIJR = "ListModelImportJobsRequest";
var _LMIJRi = "ListModelImportJobsResponse";
var _LMIJRis = "ListModelInvocationJobsRequest";
var _LMIJRist = "ListModelInvocationJobsResponse";
var _LMIJi = "ListModelInvocationJobs";
var _LMME = "ListMarketplaceModelEndpoints";
var _LMMER = "ListMarketplaceModelEndpointsRequest";
var _LMMERi = "ListMarketplaceModelEndpointsResponse";
var _LPMT = "ListProvisionedModelThroughputs";
var _LPMTR = "ListProvisionedModelThroughputsRequest";
var _LPMTRi = "ListProvisionedModelThroughputsResponse";
var _LPR = "ListPromptRouters";
var _LPRR = "ListPromptRoutersRequest";
var _LPRRi = "ListPromptRoutersResponse";
var _LT = "LegalTerm";
var _LTFR = "ListTagsForResource";
var _LTFRR = "ListTagsForResourceRequest";
var _LTFRRi = "ListTagsForResourceResponse";
var _M = "Message";
var _MAS = "MetadataAttributeSchema";
var _MASL = "MetadataAttributeSchemaList";
var _MCFR = "MetadataConfigurationForReranking";
var _MCJS = "ModelCopyJobSummary";
var _MCJSo = "ModelCustomizationJobSummary";
var _MCJSod = "ModelCopyJobSummaries";
var _MCJSode = "ModelCustomizationJobSummaries";
var _MDS = "ModelDataSource";
var _MIJIDC = "ModelInvocationJobInputDataConfig";
var _MIJODC = "ModelInvocationJobOutputDataConfig";
var _MIJS = "ModelImportJobSummary";
var _MIJSIDC = "ModelInvocationJobS3InputDataConfig";
var _MIJSODC = "ModelInvocationJobS3OutputDataConfig";
var _MIJSo = "ModelInvocationJobSummary";
var _MIJSod = "ModelImportJobSummaries";
var _MIJSode = "ModelInvocationJobSummaries";
var _MME = "MarketplaceModelEndpoint";
var _MMES = "MarketplaceModelEndpointSummary";
var _MMESa = "MarketplaceModelEndpointSummaries";
var _MN = "MetricName";
var _O = "Offer";
var _OC = "OrchestrationConfiguration";
var _ODC = "OutputDataConfig";
var _Of = "Offers";
var _PC = "PerformanceConfiguration";
var _PEGC = "PutEnforcedGuardrailConfiguration";
var _PEGCR = "PutEnforcedGuardrailConfigurationRequest";
var _PEGCRu = "PutEnforcedGuardrailConfigurationResponse";
var _PMILC = "PutModelInvocationLoggingConfiguration";
var _PMILCR = "PutModelInvocationLoggingConfigurationRequest";
var _PMILCRu = "PutModelInvocationLoggingConfigurationResponse";
var _PMS = "ProvisionedModelSummary";
var _PMSr = "ProvisionedModelSummaries";
var _PRD = "PromptRouterDescription";
var _PRS = "PromptRouterSummary";
var _PRSr = "PromptRouterSummaries";
var _PRTM = "PromptRouterTargetModel";
var _PRTMr = "PromptRouterTargetModels";
var _PT = "PricingTerm";
var _PTr = "PromptTemplate";
var _PUCFMA = "PutUseCaseForModelAccess";
var _PUCFMAR = "PutUseCaseForModelAccessRequest";
var _PUCFMARu = "PutUseCaseForModelAccessResponse";
var _QTC = "QueryTransformationConfiguration";
var _RAGC = "RetrieveAndGenerateConfiguration";
var _RAGCo = "RAGConfig";
var _RC = "RetrieveConfig";
var _RCa = "RagConfigs";
var _RCat = "RateCard";
var _RCo = "RoutingCriteria";
var _RF = "RetrievalFilter";
var _RFL = "RetrievalFilterList";
var _RFTC = "RFTConfig";
var _RFTHP = "RFTHyperParameters";
var _RIUE = "ResourceInUseException";
var _RMBF = "RequestMetadataBaseFilters";
var _RMF = "RequestMetadataFilters";
var _RMFL = "RequestMetadataFiltersList";
var _RMM = "RequestMetadataMap";
var _RMME = "RegisterMarketplaceModelEndpoint";
var _RMMER = "RegisterMarketplaceModelEndpointRequest";
var _RMMERe = "RegisterMarketplaceModelEndpointResponse";
var _RMSMC = "RerankingMetadataSelectiveModeConfiguration";
var _RNFE = "ResourceNotFoundException";
var _RS = "RatingScale";
var _RSI = "RatingScaleItem";
var _RSIV = "RatingScaleItemValue";
var _SARPBW = "StartAutomatedReasoningPolicyBuildWorkflow";
var _SARPBWR = "StartAutomatedReasoningPolicyBuildWorkflowRequest";
var _SARPBWRt = "StartAutomatedReasoningPolicyBuildWorkflowResponse";
var _SARPTW = "StartAutomatedReasoningPolicyTestWorkflow";
var _SARPTWR = "StartAutomatedReasoningPolicyTestWorkflowRequest";
var _SARPTWRt = "StartAutomatedReasoningPolicyTestWorkflowResponse";
var _SC = "S3Config";
var _SD = "StatusDetails";
var _SDS = "S3DataSource";
var _SEJ = "StopEvaluationJob";
var _SEJR = "StopEvaluationJobRequest";
var _SEJRt = "StopEvaluationJobResponse";
var _SMCJ = "StopModelCustomizationJob";
var _SMCJR = "StopModelCustomizationJobRequest";
var _SMCJRt = "StopModelCustomizationJobResponse";
var _SME = "SageMakerEndpoint";
var _SMIJ = "StopModelInvocationJob";
var _SMIJR = "StopModelInvocationJobRequest";
var _SMIJRt = "StopModelInvocationJobResponse";
var _SOD = "S3ObjectDoc";
var _SQEE = "ServiceQuotaExceededException";
var _ST = "SupportTerm";
var _SUE = "ServiceUnavailableException";
var _T = "Tag";
var _TD = "TermDetails";
var _TDC = "TrainingDataConfig";
var _TDr = "TrainingDetails";
var _TE = "ThrottlingException";
var _TIC = "TextInferenceConfig";
var _TL = "TagList";
var _TM = "TrainingMetrics";
var _TMC = "TeacherModelConfig";
var _TMTE = "TooManyTagsException";
var _TPT = "TextPromptTemplate";
var _TR = "TagResource";
var _TRR = "TagResourceRequest";
var _TRRa = "TagResourceResponse";
var _UARP = "UpdateAutomatedReasoningPolicy";
var _UARPA = "UpdateAutomatedReasoningPolicyAnnotations";
var _UARPAR = "UpdateAutomatedReasoningPolicyAnnotationsRequest";
var _UARPARp = "UpdateAutomatedReasoningPolicyAnnotationsResponse";
var _UARPR = "UpdateAutomatedReasoningPolicyRequest";
var _UARPRp = "UpdateAutomatedReasoningPolicyResponse";
var _UARPTC = "UpdateAutomatedReasoningPolicyTestCase";
var _UARPTCR = "UpdateAutomatedReasoningPolicyTestCaseRequest";
var _UARPTCRp = "UpdateAutomatedReasoningPolicyTestCaseResponse";
var _UCMD = "UpdateCustomModelDeployment";
var _UCMDR = "UpdateCustomModelDeploymentRequest";
var _UCMDRp = "UpdateCustomModelDeploymentResponse";
var _UG = "UpdateGuardrail";
var _UGR = "UpdateGuardrailRequest";
var _UGRp = "UpdateGuardrailResponse";
var _UMME = "UpdateMarketplaceModelEndpoint";
var _UMMER = "UpdateMarketplaceModelEndpointRequest";
var _UMMERp = "UpdateMarketplaceModelEndpointResponse";
var _UPMT = "UpdateProvisionedModelThroughput";
var _UPMTR = "UpdateProvisionedModelThroughputRequest";
var _UPMTRp = "UpdateProvisionedModelThroughputResponse";
var _UR = "UntagResource";
var _URR = "UntagResourceRequest";
var _URRn = "UntagResourceResponse";
var _V = "Validator";
var _VC = "VpcConfig";
var _VD = "ValidationDetails";
var _VDC = "ValidationDataConfig";
var _VE = "ValidationException";
var _VM = "ValidatorMetric";
var _VMa = "ValidationMetrics";
var _VSBRC = "VectorSearchBedrockRerankingConfiguration";
var _VSBRMC = "VectorSearchBedrockRerankingModelConfiguration";
var _VSRC = "VectorSearchRerankingConfiguration";
var _VT = "ValidityTerm";
var _Va = "Validators";
var _a = "annotation";
var _aA = "agreementAvailability";
var _aAn = "andAll";
var _aD = "agreementDuration";
var _aDDE = "audioDataDeliveryEnabled";
var _aE = "alternateExpression";
var _aEc = "acceptEula";
var _aMRF = "additionalModelRequestFields";
var _aR = "addRule";
var _aRFNL = "addRuleFromNaturalLanguage";
var _aRP = "automatedReasoningPolicy";
var _aRPBWS = "automatedReasoningPolicyBuildWorkflowSummaries";
var _aRPC = "automatedReasoningPolicyConfig";
var _aRPS = "automatedReasoningPolicySummaries";
var _aS = "authorizationStatus";
var _aSH = "annotationSetHash";
var _aT = "applicationType";
var _aTE = "applicationTypeEquals";
var _aTFR = "aggregatedTestFindingsResult";
var _aTV = "addTypeValue";
var _aTd = "addType";
var _aTs = "assetType";
var _aV = "addVariable";
var _ac = "action";
var _an = "annotations";
var _ar = "arn";
var _au = "automated";
var _bC = "byteContent";
var _bCT = "byCustomizationType";
var _bEM = "bedrockEvaluatorModels";
var _bIM = "blockedInputMessaging";
var _bIT = "byInferenceType";
var _bKBI = "bedrockKnowledgeBaseIdentifiers";
var _bL = "buildLog";
var _bM = "bedrockModel";
var _bMA = "baseModelArn";
var _bMAE = "baseModelArnEquals";
var _bMI = "baseModelIdentifier";
var _bMIe = "bedrockModelIdentifiers";
var _bMN = "baseModelName";
var _bN = "bucketName";
var _bOM = "blockedOutputsMessaging";
var _bOMy = "byOutputModality";
var _bP = "byProvider";
var _bRC = "bedrockRerankingConfiguration";
var _bS = "buildSteps";
var _bSa = "batchSize";
var _bWA = "buildWorkflowAssets";
var _bWI = "buildWorkflowId";
var _bWT = "buildWorkflowType";
var _c = "client";
var _cA = "createdAt";
var _cAr = "createdAfter";
var _cB = "createdBy";
var _cBr = "createdBefore";
var _cC = "customizationConfig";
var _cD = "commitmentDuration";
var _cEKI = "customerEncryptionKeyId";
var _cET = "commitmentExpirationTime";
var _cF = "copyFrom";
var _cFS = "claimsFalseScenario";
var _cGP = "contextualGroundingPolicy";
var _cGPC = "contextualGroundingPolicyConfig";
var _cI = "configId";
var _cM = "customMetrics";
var _cMA = "customModelArn";
var _cMC = "customMetricConfig";
var _cMD = "customMetricDefinition";
var _cMDA = "customModelDeploymentArn";
var _cMDI = "customModelDeploymentIdentifier";
var _cMDN = "customModelDeploymentName";
var _cMEMI = "customMetricsEvaluatorModelIdentifiers";
var _cMKKI = "customModelKmsKeyId";
var _cMN = "customModelName";
var _cMT = "customModelTags";
var _cMU = "customModelUnits";
var _cMUPMC = "customModelUnitsPerModelCopy";
var _cMUV = "customModelUnitsVersion";
var _cP = "contentPolicy";
var _cPC = "contentPolicyConfig";
var _cR = "contradictingRules";
var _cRC = "crossRegionConfig";
var _cRD = "crossRegionDetails";
var _cRT = "clientRequestToken";
var _cRo = "conflictingRules";
var _cS = "customizationsSupported";
var _cT = "confidenceThreshold";
var _cTA = "creationTimeAfter";
var _cTB = "creationTimeBefore";
var _cTS = "claimsTrueScenario";
var _cTo = "contentType";
var _cTr = "creationTime";
var _cTu = "customizationType";
var _cWC = "cloudWatchConfig";
var _cl = "claims";
var _co = "confidence";
var _cod = "code";
var _con = "context";
var _cont = "content";
var _d = "description";
var _dC = "distillationConfig";
var _dCT = "documentContentType";
var _dD = "documentDescription";
var _dH = "definitionHash";
var _dL = "datasetLocation";
var _dMA = "desiredModelArn";
var _dMC = "datasetMetricConfigs";
var _dMI = "desiredModelId";
var _dMU = "desiredModelUnits";
var _dN = "documentName";
var _dPD = "dataProcessingDetails";
var _dPMN = "desiredProvisionedModelName";
var _dR = "deleteRule";
var _dRS = "disjointRuleSets";
var _dS = "differenceScenarios";
var _dT = "deleteType";
var _dTV = "deleteTypeValue";
var _dV = "deleteVariable";
var _da = "data";
var _dat = "dataset";
var _de = "definition";
var _di = "dimension";
var _do = "document";
var _doc = "documents";
var _e = "error";
var _eA = "endpointArn";
var _eAFR = "expectedAggregatedFindingsResult";
var _eAn = "entitlementAvailability";
var _eC = "evaluationConfig";
var _eCn = "endpointConfig";
var _eCp = "epochCount";
var _eDDE = "embeddingDataDeliveryEnabled";
var _eI = "endpointIdentifier";
var _eIv = "evalInterval";
var _eJ = "evaluationJobs";
var _eM = "errorMessage";
var _eMC = "evaluatorModelConfig";
var _eMI = "evaluatorModelIdentifiers";
var _eN = "endpointName";
var _eR = "expectedResult";
var _eRx = "executionRole";
var _eS = "endpointStatus";
var _eSC = "externalSourcesConfiguration";
var _eSM = "endpointStatusMessage";
var _eT = "endTime";
var _eTT = "evaluationTaskTypes";
var _en = "entries";
var _ena = "enabled";
var _eq = "equals";
var _er = "errors";
var _ex = "expression";
var _exa = "examples";
var _f = "feedback";
var _fC = "filtersConfig";
var _fD = "formData";
var _fDA = "flowDefinitionArn";
var _fM = "fallbackModel";
var _fMA = "foundationModelArn";
var _fMAE = "foundationModelArnEquals";
var _fMa = "failureMessage";
var _fMai = "failureMessages";
var _fN = "fieldName";
var _fR = "failureRecommendations";
var _fTE = "fieldsToExclude";
var _fTI = "fieldsToInclude";
var _fV = "floatValue";
var _fi = "filters";
var _fil = "filter";
var _fo = "force";
var _g = "guardrails";
var _gA = "guardrailArn";
var _gC = "guardContent";
var _gCe = "generationConfiguration";
var _gCr = "graderConfig";
var _gCu = "guardrailConfiguration";
var _gCua = "guardrailsConfig";
var _gI = "guardrailIdentifier";
var _gIC = "guardrailInferenceConfig";
var _gIu = "guardrailId";
var _gPA = "guardrailProfileArn";
var _gPI = "guardrailProfileIdentifier";
var _gPIu = "guardrailProfileId";
var _gT = "greaterThan";
var _gTC = "generatedTestCases";
var _gTOE = "greaterThanOrEquals";
var _gV = "guardrailVersion";
var _h = "human";
var _hE = "httpError";
var _hH = "httpHeader";
var _hP = "hyperParameters";
var _hQ = "httpQuery";
var _hWC = "humanWorkflowConfig";
var _ht = "http";
var _i = "id";
var _iA = "inputAction";
var _iC = "inferenceConfig";
var _iCS = "inferenceConfigSummary";
var _iCn = "ingestContent";
var _iDC = "inputDataConfig";
var _iDDE = "imageDataDeliveryEnabled";
var _iE = "inputEnabled";
var _iFC = "implicitFilterConfiguration";
var _iIC = "initialInstanceCount";
var _iJS = "invocationJobSummaries";
var _iLC = "invocationLogsConfig";
var _iLS = "invocationLogSource";
var _iM = "inputModalities";
var _iMA = "importedModelArn";
var _iMKKA = "importedModelKmsKeyArn";
var _iMKKI = "importedModelKmsKeyId";
var _iMN = "importedModelName";
var _iMT = "importedModelTags";
var _iMTn = "inferenceMaxTokens";
var _iO = "isOwned";
var _iP = "inferenceParams";
var _iPA = "inferenceProfileArn";
var _iPI = "inferenceProfileIdentifier";
var _iPIn = "inferenceProfileId";
var _iPN = "inferenceProfileName";
var _iPS = "inferenceProfileSummaries";
var _iS = "instructSupported";
var _iSI = "inferenceSourceIdentifier";
var _iSn = "inputStrength";
var _iT = "inputTags";
var _iTS = "inferenceTypesSupported";
var _iTd = "idempotencyToken";
var _iTn = "instanceType";
var _id = "identifier";
var _im = "impossible";
var _in = "instructions";
var _in_ = "in";
var _inv = "invalid";
var _jA = "jobArn";
var _jD = "jobDescription";
var _jET = "jobExpirationTime";
var _jI = "jobIdentifier";
var _jIo = "jobIdentifiers";
var _jN = "jobName";
var _jS = "jobStatus";
var _jSo = "jobSummaries";
var _jT = "jobTags";
var _jTo = "jobType";
var _k = "key";
var _kBC = "knowledgeBaseConfiguration";
var _kBCn = "knowledgeBaseConfig";
var _kBI = "knowledgeBaseId";
var _kBRC = "knowledgeBaseRetrievalConfiguration";
var _kEK = "kmsEncryptionKey";
var _kIC = "kbInferenceConfig";
var _kKA = "kmsKeyArn";
var _kKI = "kmsKeyId";
var _kP = "keyPrefix";
var _l = "logic";
var _lA = "lambdaArn";
var _lC = "loggingConfig";
var _lCi = "listContains";
var _lDDSC = "largeDataDeliveryS3Config";
var _lG = "lambdaGrader";
var _lGN = "logGroupName";
var _lMT = "lastModifiedTime";
var _lR = "learningRate";
var _lT = "legalTerm";
var _lTOE = "lessThanOrEquals";
var _lTe = "lessThan";
var _lUA = "lastUpdatedAt";
var _lUASH = "lastUpdatedAnnotationSetHash";
var _lUDH = "lastUpdatedDefinitionHash";
var _lW = "logicWarning";
var _la = "latency";
var _m = "message";
var _mA = "modelArn";
var _mAE = "modelArnEquals";
var _mAe = "metadataAttributes";
var _mAo = "modelArchitecture";
var _mC = "modelConfiguration";
var _mCJS = "modelCopyJobSummaries";
var _mCJSo = "modelCustomizationJobSummaries";
var _mCS = "modelConfigSummary";
var _mCe = "metadataConfiguration";
var _mD = "modelDetails";
var _mDN = "modelDeploymentName";
var _mDS = "modelDataSource";
var _mDSo = "modelDeploymentSummaries";
var _mI = "modelIdentifier";
var _mIJS = "modelImportJobSummaries";
var _mIo = "modelId";
var _mIod = "modelIdentifiers";
var _mKKA = "modelKmsKeyArn";
var _mKKI = "modelKmsKeyId";
var _mL = "modelLifecycle";
var _mME = "marketplaceModelEndpoint";
var _mMEa = "marketplaceModelEndpoints";
var _mN = "modelName";
var _mNe = "metricNames";
var _mPL = "maxPromptLength";
var _mR = "maxResults";
var _mRLFI = "maxResponseLengthForInference";
var _mS = "modelSource";
var _mSC = "modelSourceConfig";
var _mSE = "modelSourceEquals";
var _mSI = "modelSourceIdentifier";
var _mSo = "modelStatus";
var _mSod = "modelSummaries";
var _mT = "messageType";
var _mTa = "maxTokens";
var _mTo = "modelTags";
var _mU = "modelUnits";
var _mWL = "managedWordLists";
var _mWLC = "managedWordListsConfig";
var _me = "messages";
var _mo = "models";
var _mu = "mutation";
var _n = "name";
var _nC = "nameContains";
var _nE = "notEquals";
var _nI = "notIn";
var _nL = "naturalLanguage";
var _nN = "newName";
var _nOR = "numberOfResults";
var _nORR = "numberOfRerankedResults";
var _nT = "nextToken";
var _nTo = "noTranslations";
var _nV = "newValue";
var _o = "owner";
var _oA = "outputAction";
var _oAI = "ownerAccountId";
var _oAr = "orAll";
var _oC = "orchestrationConfiguration";
var _oDC = "outputDataConfig";
var _oE = "outputEnabled";
var _oI = "offerId";
var _oM = "outputModalities";
var _oMA = "outputModelArn";
var _oMKKA = "outputModelKmsKeyArn";
var _oMN = "outputModelName";
var _oMNC = "outputModelNameContains";
var _oS = "outputStrength";
var _oST = "overrideSearchType";
var _oT = "offerToken";
var _oTf = "offerType";
var _of = "offers";
var _op = "options";
var _p = "premises";
var _pA = "policyArn";
var _pC = "performanceConfig";
var _pD = "policyDefinition";
var _pDR = "policyDefinitionRule";
var _pDT = "policyDefinitionType";
var _pDV = "policyDefinitionVariable";
var _pE = "priorElement";
var _pEC = "piiEntitiesConfig";
var _pEi = "piiEntities";
var _pI = "policyId";
var _pIS = "precomputedInferenceSource";
var _pISI = "precomputedInferenceSourceIdentifiers";
var _pMA = "provisionedModelArn";
var _pMI = "provisionedModelId";
var _pMN = "provisionedModelName";
var _pMS = "provisionedModelSummaries";
var _pN = "providerName";
var _pRA = "promptRouterArn";
var _pRAo = "policyRepairAssets";
var _pRN = "promptRouterName";
var _pRS = "promptRouterSummaries";
var _pRSC = "precomputedRagSourceConfig";
var _pRSI = "precomputedRagSourceIdentifiers";
var _pS = "policyScenarios";
var _pT = "promptTemplate";
var _pVA = "policyVersionArn";
var _pa = "pattern";
var _pl = "planning";
var _po = "policies";
var _pr = "price";
var _qC = "queryContent";
var _qR = "qualityReport";
var _qTC = "queryTransformationConfiguration";
var _r = "rule";
var _rA = "roleArn";
var _rAGC = "retrieveAndGenerateConfig";
var _rAGSC = "retrieveAndGenerateSourceConfig";
var _rARN = "resourceARN";
var _rAe = "regionAvailability";
var _rC = "ruleCount";
var _rCS = "ragConfigSummary";
var _rCa = "rateCard";
var _rCag = "ragConfigs";
var _rCe = "regexesConfig";
var _rCer = "rerankingConfiguration";
var _rCet = "retrievalConfiguration";
var _rCetr = "retrieveConfig";
var _rCf = "rftConfig";
var _rCo = "routingCriteria";
var _rE = "reasoningEffort";
var _rI = "ruleId";
var _rIa = "ragIdentifiers";
var _rIu = "ruleIds";
var _rM = "ratingMethod";
var _rMF = "requestMetadataFilters";
var _rN = "resourceName";
var _rPD = "refundPolicyDescription";
var _rQD = "responseQualityDifference";
var _rS = "ratingScale";
var _rSC = "retrieveSourceConfig";
var _rSI = "ragSourceIdentifier";
var _rSS = "responseStreamingSupported";
var _re = "regexes";
var _ru = "rules";
var _s = "status";
var _sAE = "sourceAccountEquals";
var _sAI = "sourceAccountId";
var _sB = "sortBy";
var _sBO = "s3BucketOwner";
var _sC = "s3Config";
var _sCo = "sourceContent";
var _sCt = "stringContains";
var _sD = "statusDetails";
var _sDS = "s3DataSource";
var _sE = "scenarioExpression";
var _sEKI = "s3EncryptionKeyId";
var _sEt = "statusEquals";
var _sGI = "securityGroupIds";
var _sI = "subnetIds";
var _sIDC = "s3InputDataConfig";
var _sIF = "s3InputFormat";
var _sIP = "sensitiveInformationPolicy";
var _sIPC = "sensitiveInformationPolicyConfig";
var _sL = "s3Location";
var _sM = "statusMessage";
var _sMA = "sourceModelArn";
var _sMAE = "sourceModelArnEquals";
var _sMC = "selectiveModeConfiguration";
var _sMN = "sourceModelName";
var _sMa = "sageMaker";
var _sMe = "selectionMode";
var _sO = "sortOrder";
var _sODC = "s3OutputDataConfig";
var _sR = "supportingRules";
var _sRt = "statusReasons";
var _sS = "stopSequences";
var _sT = "sourceType";
var _sTA = "submitTimeAfter";
var _sTB = "submitTimeBefore";
var _sTu = "submitTime";
var _sTup = "supportTerm";
var _sU = "s3Uri";
var _sV = "stringValue";
var _sW = "startsWith";
var _sa = "satisfiable";
var _sc = "scenario";
var _se = "server";
var _sm = "smithy.ts.sdk.synthetic.com.amazonaws.bedrock";
var _so = "sources";
var _st = "statements";
var _t = "translation";
var _tA = "translationAmbiguous";
var _tC = "typeCount";
var _tCI = "testCaseId";
var _tCIe = "testCaseIds";
var _tCe = "testCase";
var _tCes = "testCases";
var _tCi = "tierConfig";
var _tCo = "topicsConfig";
var _tCoo = "tooComplex";
var _tD = "termDetails";
var _tDC = "trainingDataConfig";
var _tDDE = "textDataDeliveryEnabled";
var _tDIH = "timeoutDurationInHours";
var _tDr = "trainingDetails";
var _tE = "typeEquals";
var _tF = "testFindings";
var _tIC = "textInferenceConfig";
var _tK = "tagKeys";
var _tL = "trainingLoss";
var _tM = "trainingMetrics";
var _tMA = "targetModelArn";
var _tMC = "teacherModelConfig";
var _tMI = "teacherModelIdentifier";
var _tMKKA = "targetModelKmsKeyArn";
var _tMN = "targetModelName";
var _tMNC = "targetModelNameContains";
var _tMT = "targetModelTags";
var _tN = "typeName";
var _tNi = "tierName";
var _tP = "topicPolicy";
var _tPC = "topicPolicyConfig";
var _tPT = "textPromptTemplate";
var _tPo = "topP";
var _tR = "testResult";
var _tRR = "testRunResult";
var _tRS = "testRunStatus";
var _tRe = "testResults";
var _tSPP = "trainingSamplePerPrompt";
var _tT = "taskType";
var _ta = "tags";
var _te = "text";
var _tem = "temperature";
var _th = "threshold";
var _ti = "tier";
var _to = "topics";
var _tr = "translations";
var _ty = "type";
var _typ = "types";
var _u = "unit";
var _uA = "updatedAt";
var _uB = "updatedBy";
var _uBPT = "usageBasedPricingTerm";
var _uC = "untranslatedClaims";
var _uD = "updateDetails";
var _uFRF = "updateFromRulesFeedback";
var _uFSF = "updateFromScenarioFeedback";
var _uP = "untranslatedPremises";
var _uPR = "usePromptResponse";
var _uR = "updateRule";
var _uS = "updateStatus";
var _uT = "unusedTypes";
var _uTV = "unusedTypeValues";
var _uTVp = "updateTypeValue";
var _uTp = "updateType";
var _uV = "unusedVariables";
var _uVp = "updateVariable";
var _ur = "url";
var _uri = "uri";
var _v = "values";
var _vC = "variableCount";
var _vCp = "vpcConfig";
var _vD = "validationDetails";
var _vDC = "validationDataConfig";
var _vDDE = "videoDataDeliveryEnabled";
var _vL = "validationLoss";
var _vM = "validationMetrics";
var _vN = "valueName";
var _vSC = "vectorSearchConfiguration";
var _vT = "validityTerm";
var _va = "value";
var _val = "validators";
var _vali = "valid";
var _var = "variable";
var _vari = "variables";
var _ve = "version";
var _vp = "vpc";
var _w = "words";
var _wC = "workflowContent";
var _wCo = "wordsConfig";
var _wP = "wordPolicy";
var _wPC = "wordPolicyConfig";
var _xact = "x-amz-client-token";
var n0 = "com.amazonaws.bedrock";
var AutomatedReasoningLogicStatementContent = [0, n0, _ARLSC, 8, 0];
var AutomatedReasoningNaturalLanguageStatementContent = [0, n0, _ARNLSC, 8, 0];
var AutomatedReasoningPolicyAnnotationFeedbackNaturalLanguage = [0, n0, _ARPAFNL, 8, 0];
var AutomatedReasoningPolicyAnnotationIngestContent = [0, n0, _ARPAIC, 8, 0];
var AutomatedReasoningPolicyAnnotationRuleNaturalLanguage = [0, n0, _ARPARNL, 8, 0];
var AutomatedReasoningPolicyBuildDocumentBlob = [0, n0, _ARPBDB, 8, 21];
var AutomatedReasoningPolicyBuildDocumentDescription = [0, n0, _ARPBDD, 8, 0];
var AutomatedReasoningPolicyBuildDocumentName = [0, n0, _ARPBDN, 8, 0];
var AutomatedReasoningPolicyDefinitionRuleAlternateExpression = [0, n0, _ARPDRAE, 8, 0];
var AutomatedReasoningPolicyDefinitionRuleExpression = [0, n0, _ARPDRE, 8, 0];
var AutomatedReasoningPolicyDefinitionTypeDescription = [0, n0, _ARPDTD, 8, 0];
var AutomatedReasoningPolicyDefinitionTypeName = [0, n0, _ARPDTN, 8, 0];
var AutomatedReasoningPolicyDefinitionTypeValueDescription = [0, n0, _ARPDTVD, 8, 0];
var AutomatedReasoningPolicyDefinitionVariableDescription = [0, n0, _ARPDVD, 8, 0];
var AutomatedReasoningPolicyDefinitionVariableName = [0, n0, _ARPDVN, 8, 0];
var AutomatedReasoningPolicyDescription = [0, n0, _ARPD, 8, 0];
var AutomatedReasoningPolicyName = [0, n0, _ARPN, 8, 0];
var AutomatedReasoningPolicyScenarioAlternateExpression = [0, n0, _ARPSAE, 8, 0];
var AutomatedReasoningPolicyScenarioExpression = [0, n0, _ARPSE, 8, 0];
var AutomatedReasoningPolicyTestGuardContent = [0, n0, _ARPTGC, 8, 0];
var AutomatedReasoningPolicyTestQueryContent = [0, n0, _ARPTQC, 8, 0];
var ByteContentBlob = [0, n0, _BCB, 8, 21];
var EvaluationDatasetName = [0, n0, _EDN, 8, 0];
var EvaluationJobDescription = [0, n0, _EJD, 8, 0];
var EvaluationJobIdentifier = [0, n0, _EJI, 8, 0];
var EvaluationMetricDescription = [0, n0, _EMD, 8, 0];
var EvaluationMetricName = [0, n0, _EMN, 8, 0];
var EvaluationModelInferenceParams = [0, n0, _EMIP, 8, 0];
var GuardrailBlockedMessaging = [0, n0, _GBM, 8, 0];
var GuardrailContentFilterAction = [0, n0, _GCFA, 8, 0];
var GuardrailContentFiltersTierName = [0, n0, _GCFTN, 8, 0];
var GuardrailContextualGroundingAction = [0, n0, _GCGA, 8, 0];
var GuardrailDescription = [0, n0, _GD, 8, 0];
var GuardrailFailureRecommendation = [0, n0, _GFR, 8, 0];
var GuardrailModality = [0, n0, _GM, 8, 0];
var GuardrailName = [0, n0, _GN, 8, 0];
var GuardrailStatusReason = [0, n0, _GSR, 8, 0];
var GuardrailTopicAction = [0, n0, _GTA, 8, 0];
var GuardrailTopicDefinition = [0, n0, _GTD, 8, 0];
var GuardrailTopicExample = [0, n0, _GTE, 8, 0];
var GuardrailTopicName = [0, n0, _GTN, 8, 0];
var GuardrailTopicsTierName = [0, n0, _GTTN, 8, 0];
var GuardrailWordAction = [0, n0, _GWA, 8, 0];
var HumanTaskInstructions = [0, n0, _HTI, 8, 0];
var Identifier = [0, n0, _I, 8, 0];
var InferenceProfileDescription = [0, n0, _IPD, 8, 0];
var Message = [0, n0, _M, 8, 0];
var MetricName = [0, n0, _MN, 8, 0];
var PromptRouterDescription = [0, n0, _PRD, 8, 0];
var TextPromptTemplate = [0, n0, _TPT, 8, 0];
var AccessDeniedException$ = [
  -3,
  n0,
  _ADE,
  { [_e]: _c, [_hE]: 403 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(AccessDeniedException$, AccessDeniedException);
var AccountEnforcedGuardrailInferenceInputConfiguration$ = [
  3,
  n0,
  _AEGIIC,
  0,
  [_gI, _gV, _iT],
  [0, 0, 0]
];
var AccountEnforcedGuardrailOutputConfiguration$ = [
  3,
  n0,
  _AEGOC,
  0,
  [_cI, _gA, _gIu, _iT, _gV, _cA, _cB, _uA, _uB, _o],
  [0, 0, 0, 0, 0, 5, 0, 5, 0, 0]
];
var AgreementAvailability$ = [
  3,
  n0,
  _AA,
  0,
  [_s, _eM],
  [0, 0]
];
var AutomatedEvaluationConfig$ = [
  3,
  n0,
  _AEC,
  0,
  [_dMC, _eMC, _cMC],
  [[() => EvaluationDatasetMetricConfigs, 0], () => EvaluatorModelConfig$, [() => AutomatedEvaluationCustomMetricConfig$, 0]]
];
var AutomatedEvaluationCustomMetricConfig$ = [
  3,
  n0,
  _AECMC,
  0,
  [_cM, _eMC],
  [[() => AutomatedEvaluationCustomMetrics, 0], () => CustomMetricEvaluatorModelConfig$]
];
var AutomatedReasoningCheckImpossibleFinding$ = [
  3,
  n0,
  _ARCIF,
  0,
  [_t, _cR, _lW],
  [[() => AutomatedReasoningCheckTranslation$, 0], () => AutomatedReasoningCheckRuleList, [() => AutomatedReasoningCheckLogicWarning$, 0]]
];
var AutomatedReasoningCheckInputTextReference$ = [
  3,
  n0,
  _ARCITR,
  0,
  [_te],
  [[() => AutomatedReasoningNaturalLanguageStatementContent, 0]]
];
var AutomatedReasoningCheckInvalidFinding$ = [
  3,
  n0,
  _ARCIFu,
  0,
  [_t, _cR, _lW],
  [[() => AutomatedReasoningCheckTranslation$, 0], () => AutomatedReasoningCheckRuleList, [() => AutomatedReasoningCheckLogicWarning$, 0]]
];
var AutomatedReasoningCheckLogicWarning$ = [
  3,
  n0,
  _ARCLW,
  0,
  [_ty, _p, _cl],
  [0, [() => AutomatedReasoningLogicStatementList, 0], [() => AutomatedReasoningLogicStatementList, 0]]
];
var AutomatedReasoningCheckNoTranslationsFinding$ = [
  3,
  n0,
  _ARCNTF,
  0,
  [],
  []
];
var AutomatedReasoningCheckRule$ = [
  3,
  n0,
  _ARCR,
  0,
  [_i, _pVA],
  [0, 0]
];
var AutomatedReasoningCheckSatisfiableFinding$ = [
  3,
  n0,
  _ARCSF,
  0,
  [_t, _cTS, _cFS, _lW],
  [[() => AutomatedReasoningCheckTranslation$, 0], [() => AutomatedReasoningCheckScenario$, 0], [() => AutomatedReasoningCheckScenario$, 0], [() => AutomatedReasoningCheckLogicWarning$, 0]]
];
var AutomatedReasoningCheckScenario$ = [
  3,
  n0,
  _ARCS,
  0,
  [_st],
  [[() => AutomatedReasoningLogicStatementList, 0]]
];
var AutomatedReasoningCheckTooComplexFinding$ = [
  3,
  n0,
  _ARCTCF,
  0,
  [],
  []
];
var AutomatedReasoningCheckTranslation$ = [
  3,
  n0,
  _ARCT,
  0,
  [_p, _cl, _uP, _uC, _co],
  [[() => AutomatedReasoningLogicStatementList, 0], [() => AutomatedReasoningLogicStatementList, 0], [() => AutomatedReasoningCheckInputTextReferenceList, 0], [() => AutomatedReasoningCheckInputTextReferenceList, 0], 1]
];
var AutomatedReasoningCheckTranslationAmbiguousFinding$ = [
  3,
  n0,
  _ARCTAF,
  0,
  [_op, _dS],
  [[() => AutomatedReasoningCheckTranslationOptionList, 0], [() => AutomatedReasoningCheckDifferenceScenarioList, 0]]
];
var AutomatedReasoningCheckTranslationOption$ = [
  3,
  n0,
  _ARCTO,
  0,
  [_tr],
  [[() => AutomatedReasoningCheckTranslationList, 0]]
];
var AutomatedReasoningCheckValidFinding$ = [
  3,
  n0,
  _ARCVF,
  0,
  [_t, _cTS, _sR, _lW],
  [[() => AutomatedReasoningCheckTranslation$, 0], [() => AutomatedReasoningCheckScenario$, 0], () => AutomatedReasoningCheckRuleList, [() => AutomatedReasoningCheckLogicWarning$, 0]]
];
var AutomatedReasoningLogicStatement$ = [
  3,
  n0,
  _ARLS,
  0,
  [_l, _nL],
  [[() => AutomatedReasoningLogicStatementContent, 0], [() => AutomatedReasoningNaturalLanguageStatementContent, 0]]
];
var AutomatedReasoningPolicyAddRuleAnnotation$ = [
  3,
  n0,
  _ARPARA,
  0,
  [_ex],
  [[() => AutomatedReasoningPolicyDefinitionRuleExpression, 0]]
];
var AutomatedReasoningPolicyAddRuleFromNaturalLanguageAnnotation$ = [
  3,
  n0,
  _ARPARFNLA,
  0,
  [_nL],
  [[() => AutomatedReasoningPolicyAnnotationRuleNaturalLanguage, 0]]
];
var AutomatedReasoningPolicyAddRuleMutation$ = [
  3,
  n0,
  _ARPARM,
  0,
  [_r],
  [[() => AutomatedReasoningPolicyDefinitionRule$, 0]]
];
var AutomatedReasoningPolicyAddTypeAnnotation$ = [
  3,
  n0,
  _ARPATA,
  0,
  [_n, _d, _v],
  [[() => AutomatedReasoningPolicyDefinitionTypeName, 0], [() => AutomatedReasoningPolicyDefinitionTypeDescription, 0], [() => AutomatedReasoningPolicyDefinitionTypeValueList, 0]]
];
var AutomatedReasoningPolicyAddTypeMutation$ = [
  3,
  n0,
  _ARPATM,
  0,
  [_ty],
  [[() => AutomatedReasoningPolicyDefinitionType$, 0]]
];
var AutomatedReasoningPolicyAddTypeValue$ = [
  3,
  n0,
  _ARPATV,
  0,
  [_va, _d],
  [0, [() => AutomatedReasoningPolicyDefinitionTypeValueDescription, 0]]
];
var AutomatedReasoningPolicyAddVariableAnnotation$ = [
  3,
  n0,
  _ARPAVA,
  0,
  [_n, _ty, _d],
  [[() => AutomatedReasoningPolicyDefinitionVariableName, 0], [() => AutomatedReasoningPolicyDefinitionTypeName, 0], [() => AutomatedReasoningPolicyDefinitionVariableDescription, 0]]
];
var AutomatedReasoningPolicyAddVariableMutation$ = [
  3,
  n0,
  _ARPAVM,
  0,
  [_var],
  [[() => AutomatedReasoningPolicyDefinitionVariable$, 0]]
];
var AutomatedReasoningPolicyBuildLog$ = [
  3,
  n0,
  _ARPBL,
  0,
  [_en],
  [[() => AutomatedReasoningPolicyBuildLogEntryList, 0]]
];
var AutomatedReasoningPolicyBuildLogEntry$ = [
  3,
  n0,
  _ARPBLE,
  0,
  [_a, _s, _bS],
  [[() => AutomatedReasoningPolicyAnnotation$, 0], 0, [() => AutomatedReasoningPolicyBuildStepList, 0]]
];
var AutomatedReasoningPolicyBuildStep$ = [
  3,
  n0,
  _ARPBS,
  0,
  [_con, _pE, _me],
  [[() => AutomatedReasoningPolicyBuildStepContext$, 0], [() => AutomatedReasoningPolicyDefinitionElement$, 0], () => AutomatedReasoningPolicyBuildStepMessageList]
];
var AutomatedReasoningPolicyBuildStepMessage$ = [
  3,
  n0,
  _ARPBSM,
  0,
  [_m, _mT],
  [0, 0]
];
var AutomatedReasoningPolicyBuildWorkflowDocument$ = [
  3,
  n0,
  _ARPBWD,
  0,
  [_do, _dCT, _dN, _dD],
  [[() => AutomatedReasoningPolicyBuildDocumentBlob, 0], 0, [() => AutomatedReasoningPolicyBuildDocumentName, 0], [() => AutomatedReasoningPolicyBuildDocumentDescription, 0]]
];
var AutomatedReasoningPolicyBuildWorkflowRepairContent$ = [
  3,
  n0,
  _ARPBWRC,
  0,
  [_an],
  [[() => AutomatedReasoningPolicyAnnotationList, 0]]
];
var AutomatedReasoningPolicyBuildWorkflowSource$ = [
  3,
  n0,
  _ARPBWS,
  0,
  [_pD, _wC],
  [[() => AutomatedReasoningPolicyDefinition$, 0], [() => AutomatedReasoningPolicyWorkflowTypeContent$, 0]]
];
var AutomatedReasoningPolicyBuildWorkflowSummary$ = [
  3,
  n0,
  _ARPBWSu,
  0,
  [_pA, _bWI, _s, _bWT, _cA, _uA],
  [0, 0, 0, 0, 5, 5]
];
var AutomatedReasoningPolicyDefinition$ = [
  3,
  n0,
  _ARPDu,
  0,
  [_ve, _typ, _ru, _vari],
  [0, [() => AutomatedReasoningPolicyDefinitionTypeList, 0], [() => AutomatedReasoningPolicyDefinitionRuleList, 0], [() => AutomatedReasoningPolicyDefinitionVariableList, 0]]
];
var AutomatedReasoningPolicyDefinitionQualityReport$ = [
  3,
  n0,
  _ARPDQR,
  0,
  [_tC, _vC, _rC, _uT, _uTV, _uV, _cRo, _dRS],
  [1, 1, 1, [() => AutomatedReasoningPolicyDefinitionTypeNameList, 0], [() => AutomatedReasoningPolicyDefinitionTypeValuePairList, 0], [() => AutomatedReasoningPolicyDefinitionVariableNameList, 0], 64 | 0, [() => AutomatedReasoningPolicyDisjointRuleSetList, 0]]
];
var AutomatedReasoningPolicyDefinitionRule$ = [
  3,
  n0,
  _ARPDR,
  0,
  [_i, _ex, _aE],
  [0, [() => AutomatedReasoningPolicyDefinitionRuleExpression, 0], [() => AutomatedReasoningPolicyDefinitionRuleAlternateExpression, 0]]
];
var AutomatedReasoningPolicyDefinitionType$ = [
  3,
  n0,
  _ARPDT,
  0,
  [_n, _d, _v],
  [[() => AutomatedReasoningPolicyDefinitionTypeName, 0], [() => AutomatedReasoningPolicyDefinitionTypeDescription, 0], [() => AutomatedReasoningPolicyDefinitionTypeValueList, 0]]
];
var AutomatedReasoningPolicyDefinitionTypeValue$ = [
  3,
  n0,
  _ARPDTV,
  0,
  [_va, _d],
  [0, [() => AutomatedReasoningPolicyDefinitionTypeValueDescription, 0]]
];
var AutomatedReasoningPolicyDefinitionTypeValuePair$ = [
  3,
  n0,
  _ARPDTVP,
  0,
  [_tN, _vN],
  [[() => AutomatedReasoningPolicyDefinitionTypeName, 0], 0]
];
var AutomatedReasoningPolicyDefinitionVariable$ = [
  3,
  n0,
  _ARPDV,
  0,
  [_n, _ty, _d],
  [[() => AutomatedReasoningPolicyDefinitionVariableName, 0], [() => AutomatedReasoningPolicyDefinitionTypeName, 0], [() => AutomatedReasoningPolicyDefinitionVariableDescription, 0]]
];
var AutomatedReasoningPolicyDeleteRuleAnnotation$ = [
  3,
  n0,
  _ARPDRA,
  0,
  [_rI],
  [0]
];
var AutomatedReasoningPolicyDeleteRuleMutation$ = [
  3,
  n0,
  _ARPDRM,
  0,
  [_i],
  [0]
];
var AutomatedReasoningPolicyDeleteTypeAnnotation$ = [
  3,
  n0,
  _ARPDTA,
  0,
  [_n],
  [[() => AutomatedReasoningPolicyDefinitionTypeName, 0]]
];
var AutomatedReasoningPolicyDeleteTypeMutation$ = [
  3,
  n0,
  _ARPDTM,
  0,
  [_n],
  [[() => AutomatedReasoningPolicyDefinitionTypeName, 0]]
];
var AutomatedReasoningPolicyDeleteTypeValue$ = [
  3,
  n0,
  _ARPDTVu,
  0,
  [_va],
  [0]
];
var AutomatedReasoningPolicyDeleteVariableAnnotation$ = [
  3,
  n0,
  _ARPDVA,
  0,
  [_n],
  [[() => AutomatedReasoningPolicyDefinitionVariableName, 0]]
];
var AutomatedReasoningPolicyDeleteVariableMutation$ = [
  3,
  n0,
  _ARPDVM,
  0,
  [_n],
  [[() => AutomatedReasoningPolicyDefinitionVariableName, 0]]
];
var AutomatedReasoningPolicyDisjointRuleSet$ = [
  3,
  n0,
  _ARPDRS,
  0,
  [_vari, _ru],
  [[() => AutomatedReasoningPolicyDefinitionVariableNameList, 0], 64 | 0]
];
var AutomatedReasoningPolicyGeneratedTestCase$ = [
  3,
  n0,
  _ARPGTC,
  0,
  [_qC, _gC, _eAFR],
  [[() => AutomatedReasoningPolicyTestQueryContent, 0], [() => AutomatedReasoningPolicyTestGuardContent, 0], 0]
];
var AutomatedReasoningPolicyGeneratedTestCases$ = [
  3,
  n0,
  _ARPGTCu,
  0,
  [_gTC],
  [[() => AutomatedReasoningPolicyGeneratedTestCaseList, 0]]
];
var AutomatedReasoningPolicyIngestContentAnnotation$ = [
  3,
  n0,
  _ARPICA,
  0,
  [_cont],
  [[() => AutomatedReasoningPolicyAnnotationIngestContent, 0]]
];
var AutomatedReasoningPolicyPlanning$ = [
  3,
  n0,
  _ARPP,
  0,
  [],
  []
];
var AutomatedReasoningPolicyScenario$ = [
  3,
  n0,
  _ARPS,
  0,
  [_ex, _aE, _eR, _rIu],
  [[() => AutomatedReasoningPolicyScenarioExpression, 0], [() => AutomatedReasoningPolicyScenarioAlternateExpression, 0], 0, 64 | 0]
];
var AutomatedReasoningPolicyScenarios$ = [
  3,
  n0,
  _ARPSu,
  0,
  [_pS],
  [[() => AutomatedReasoningPolicyScenarioList, 0]]
];
var AutomatedReasoningPolicySummary$ = [
  3,
  n0,
  _ARPSut,
  0,
  [_pA, _n, _d, _ve, _pI, _cA, _uA],
  [0, [() => AutomatedReasoningPolicyName, 0], [() => AutomatedReasoningPolicyDescription, 0], 0, 0, 5, 5]
];
var AutomatedReasoningPolicyTestCase$ = [
  3,
  n0,
  _ARPTC,
  0,
  [_tCI, _gC, _qC, _eAFR, _cA, _uA, _cT],
  [0, [() => AutomatedReasoningPolicyTestGuardContent, 0], [() => AutomatedReasoningPolicyTestQueryContent, 0], 0, 5, 5, 1]
];
var AutomatedReasoningPolicyTestResult$ = [
  3,
  n0,
  _ARPTR,
  0,
  [_tCe, _pA, _tRS, _tF, _tRR, _aTFR, _uA],
  [[() => AutomatedReasoningPolicyTestCase$, 0], 0, 0, [() => AutomatedReasoningCheckFindingList, 0], 0, 0, 5]
];
var AutomatedReasoningPolicyUpdateFromRuleFeedbackAnnotation$ = [
  3,
  n0,
  _ARPUFRFA,
  0,
  [_rIu, _f],
  [64 | 0, [() => AutomatedReasoningPolicyAnnotationFeedbackNaturalLanguage, 0]]
];
var AutomatedReasoningPolicyUpdateFromScenarioFeedbackAnnotation$ = [
  3,
  n0,
  _ARPUFSFA,
  0,
  [_rIu, _sE, _f],
  [64 | 0, [() => AutomatedReasoningPolicyScenarioExpression, 0], [() => AutomatedReasoningPolicyAnnotationFeedbackNaturalLanguage, 0]]
];
var AutomatedReasoningPolicyUpdateRuleAnnotation$ = [
  3,
  n0,
  _ARPURA,
  0,
  [_rI, _ex],
  [0, [() => AutomatedReasoningPolicyDefinitionRuleExpression, 0]]
];
var AutomatedReasoningPolicyUpdateRuleMutation$ = [
  3,
  n0,
  _ARPURM,
  0,
  [_r],
  [[() => AutomatedReasoningPolicyDefinitionRule$, 0]]
];
var AutomatedReasoningPolicyUpdateTypeAnnotation$ = [
  3,
  n0,
  _ARPUTA,
  0,
  [_n, _nN, _d, _v],
  [[() => AutomatedReasoningPolicyDefinitionTypeName, 0], [() => AutomatedReasoningPolicyDefinitionTypeName, 0], [() => AutomatedReasoningPolicyDefinitionTypeDescription, 0], [() => AutomatedReasoningPolicyTypeValueAnnotationList, 0]]
];
var AutomatedReasoningPolicyUpdateTypeMutation$ = [
  3,
  n0,
  _ARPUTM,
  0,
  [_ty],
  [[() => AutomatedReasoningPolicyDefinitionType$, 0]]
];
var AutomatedReasoningPolicyUpdateTypeValue$ = [
  3,
  n0,
  _ARPUTV,
  0,
  [_va, _nV, _d],
  [0, 0, [() => AutomatedReasoningPolicyDefinitionTypeValueDescription, 0]]
];
var AutomatedReasoningPolicyUpdateVariableAnnotation$ = [
  3,
  n0,
  _ARPUVA,
  0,
  [_n, _nN, _d],
  [[() => AutomatedReasoningPolicyDefinitionVariableName, 0], [() => AutomatedReasoningPolicyDefinitionVariableName, 0], [() => AutomatedReasoningPolicyDefinitionVariableDescription, 0]]
];
var AutomatedReasoningPolicyUpdateVariableMutation$ = [
  3,
  n0,
  _ARPUVM,
  0,
  [_var],
  [[() => AutomatedReasoningPolicyDefinitionVariable$, 0]]
];
var BatchDeleteEvaluationJobError$ = [
  3,
  n0,
  _BDEJE,
  0,
  [_jI, _cod, _m],
  [[() => EvaluationJobIdentifier, 0], 0, 0]
];
var BatchDeleteEvaluationJobItem$ = [
  3,
  n0,
  _BDEJI,
  0,
  [_jI, _jS],
  [[() => EvaluationJobIdentifier, 0], 0]
];
var BatchDeleteEvaluationJobRequest$ = [
  3,
  n0,
  _BDEJR,
  0,
  [_jIo],
  [[() => EvaluationJobIdentifiers, 0]]
];
var BatchDeleteEvaluationJobResponse$ = [
  3,
  n0,
  _BDEJRa,
  0,
  [_er, _eJ],
  [[() => BatchDeleteEvaluationJobErrors, 0], [() => BatchDeleteEvaluationJobItems, 0]]
];
var BedrockEvaluatorModel$ = [
  3,
  n0,
  _BEM,
  0,
  [_mI],
  [0]
];
var ByteContentDoc$ = [
  3,
  n0,
  _BCD,
  0,
  [_id, _cTo, _da],
  [[() => Identifier, 0], 0, [() => ByteContentBlob, 0]]
];
var CancelAutomatedReasoningPolicyBuildWorkflowRequest$ = [
  3,
  n0,
  _CARPBWR,
  0,
  [_pA, _bWI],
  [[0, 1], [0, 1]]
];
var CancelAutomatedReasoningPolicyBuildWorkflowResponse$ = [
  3,
  n0,
  _CARPBWRa,
  0,
  [],
  []
];
var CloudWatchConfig$ = [
  3,
  n0,
  _CWC,
  0,
  [_lGN, _rA, _lDDSC],
  [0, 0, () => S3Config$]
];
var ConflictException$ = [
  -3,
  n0,
  _CE,
  { [_e]: _c, [_hE]: 400 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ConflictException$, ConflictException);
var CreateAutomatedReasoningPolicyRequest$ = [
  3,
  n0,
  _CARPR,
  0,
  [_n, _d, _cRT, _pD, _kKI, _ta],
  [[() => AutomatedReasoningPolicyName, 0], [() => AutomatedReasoningPolicyDescription, 0], [0, 4], [() => AutomatedReasoningPolicyDefinition$, 0], 0, () => TagList]
];
var CreateAutomatedReasoningPolicyResponse$ = [
  3,
  n0,
  _CARPRr,
  0,
  [_pA, _ve, _n, _d, _dH, _cA, _uA],
  [0, 0, [() => AutomatedReasoningPolicyName, 0], [() => AutomatedReasoningPolicyDescription, 0], 0, 5, 5]
];
var CreateAutomatedReasoningPolicyTestCaseRequest$ = [
  3,
  n0,
  _CARPTCR,
  0,
  [_pA, _gC, _qC, _eAFR, _cRT, _cT],
  [[0, 1], [() => AutomatedReasoningPolicyTestGuardContent, 0], [() => AutomatedReasoningPolicyTestQueryContent, 0], 0, [0, 4], 1]
];
var CreateAutomatedReasoningPolicyTestCaseResponse$ = [
  3,
  n0,
  _CARPTCRr,
  0,
  [_pA, _tCI],
  [0, 0]
];
var CreateAutomatedReasoningPolicyVersionRequest$ = [
  3,
  n0,
  _CARPVR,
  0,
  [_pA, _cRT, _lUDH, _ta],
  [[0, 1], [0, 4], 0, () => TagList]
];
var CreateAutomatedReasoningPolicyVersionResponse$ = [
  3,
  n0,
  _CARPVRr,
  0,
  [_pA, _ve, _n, _d, _dH, _cA],
  [0, 0, [() => AutomatedReasoningPolicyName, 0], [() => AutomatedReasoningPolicyDescription, 0], 0, 5]
];
var CreateCustomModelDeploymentRequest$ = [
  3,
  n0,
  _CCMDR,
  0,
  [_mDN, _mA, _d, _ta, _cRT],
  [0, 0, 0, () => TagList, [0, 4]]
];
var CreateCustomModelDeploymentResponse$ = [
  3,
  n0,
  _CCMDRr,
  0,
  [_cMDA],
  [0]
];
var CreateCustomModelRequest$ = [
  3,
  n0,
  _CCMR,
  0,
  [_mN, _mSC, _mKKA, _rA, _mTo, _cRT],
  [0, () => ModelDataSource$, 0, 0, () => TagList, [0, 4]]
];
var CreateCustomModelResponse$ = [
  3,
  n0,
  _CCMRr,
  0,
  [_mA],
  [0]
];
var CreateEvaluationJobRequest$ = [
  3,
  n0,
  _CEJR,
  0,
  [_jN, _jD, _cRT, _rA, _cEKI, _jT, _aT, _eC, _iC, _oDC],
  [0, [() => EvaluationJobDescription, 0], [0, 4], 0, 0, () => TagList, 0, [() => EvaluationConfig$, 0], [() => EvaluationInferenceConfig$, 0], () => EvaluationOutputDataConfig$]
];
var CreateEvaluationJobResponse$ = [
  3,
  n0,
  _CEJRr,
  0,
  [_jA],
  [0]
];
var CreateFoundationModelAgreementRequest$ = [
  3,
  n0,
  _CFMAR,
  0,
  [_oT, _mIo],
  [0, 0]
];
var CreateFoundationModelAgreementResponse$ = [
  3,
  n0,
  _CFMARr,
  0,
  [_mIo],
  [0]
];
var CreateGuardrailRequest$ = [
  3,
  n0,
  _CGR,
  0,
  [_n, _d, _tPC, _cPC, _wPC, _sIPC, _cGPC, _aRPC, _cRC, _bIM, _bOM, _kKI, _ta, _cRT],
  [[() => GuardrailName, 0], [() => GuardrailDescription, 0], [() => GuardrailTopicPolicyConfig$, 0], [() => GuardrailContentPolicyConfig$, 0], [() => GuardrailWordPolicyConfig$, 0], () => GuardrailSensitiveInformationPolicyConfig$, [() => GuardrailContextualGroundingPolicyConfig$, 0], () => GuardrailAutomatedReasoningPolicyConfig$, () => GuardrailCrossRegionConfig$, [() => GuardrailBlockedMessaging, 0], [() => GuardrailBlockedMessaging, 0], 0, () => TagList, [0, 4]]
];
var CreateGuardrailResponse$ = [
  3,
  n0,
  _CGRr,
  0,
  [_gIu, _gA, _ve, _cA],
  [0, 0, 0, 5]
];
var CreateGuardrailVersionRequest$ = [
  3,
  n0,
  _CGVR,
  0,
  [_gI, _d, _cRT],
  [[0, 1], [() => GuardrailDescription, 0], [0, 4]]
];
var CreateGuardrailVersionResponse$ = [
  3,
  n0,
  _CGVRr,
  0,
  [_gIu, _ve],
  [0, 0]
];
var CreateInferenceProfileRequest$ = [
  3,
  n0,
  _CIPR,
  0,
  [_iPN, _d, _cRT, _mS, _ta],
  [0, [() => InferenceProfileDescription, 0], [0, 4], () => InferenceProfileModelSource$, () => TagList]
];
var CreateInferenceProfileResponse$ = [
  3,
  n0,
  _CIPRr,
  0,
  [_iPA, _s],
  [0, 0]
];
var CreateMarketplaceModelEndpointRequest$ = [
  3,
  n0,
  _CMMER,
  0,
  [_mSI, _eCn, _aEc, _eN, _cRT, _ta],
  [0, () => EndpointConfig$, 2, 0, [0, 4], () => TagList]
];
var CreateMarketplaceModelEndpointResponse$ = [
  3,
  n0,
  _CMMERr,
  0,
  [_mME],
  [() => MarketplaceModelEndpoint$]
];
var CreateModelCopyJobRequest$ = [
  3,
  n0,
  _CMCJR,
  0,
  [_sMA, _tMN, _mKKI, _tMT, _cRT],
  [0, 0, 0, () => TagList, [0, 4]]
];
var CreateModelCopyJobResponse$ = [
  3,
  n0,
  _CMCJRr,
  0,
  [_jA],
  [0]
];
var CreateModelCustomizationJobRequest$ = [
  3,
  n0,
  _CMCJRre,
  0,
  [_jN, _cMN, _rA, _cRT, _bMI, _cTu, _cMKKI, _jT, _cMT, _tDC, _vDC, _oDC, _hP, _vCp, _cC],
  [0, 0, 0, [0, 4], 0, 0, 0, () => TagList, () => TagList, [() => TrainingDataConfig$, 0], () => ValidationDataConfig$, () => OutputDataConfig$, 128 | 0, () => VpcConfig$, () => CustomizationConfig$]
];
var CreateModelCustomizationJobResponse$ = [
  3,
  n0,
  _CMCJRrea,
  0,
  [_jA],
  [0]
];
var CreateModelImportJobRequest$ = [
  3,
  n0,
  _CMIJR,
  0,
  [_jN, _iMN, _rA, _mDS, _jT, _iMT, _cRT, _vCp, _iMKKI],
  [0, 0, 0, () => ModelDataSource$, () => TagList, () => TagList, 0, () => VpcConfig$, 0]
];
var CreateModelImportJobResponse$ = [
  3,
  n0,
  _CMIJRr,
  0,
  [_jA],
  [0]
];
var CreateModelInvocationJobRequest$ = [
  3,
  n0,
  _CMIJRre,
  0,
  [_jN, _rA, _cRT, _mIo, _iDC, _oDC, _vCp, _tDIH, _ta],
  [0, 0, [0, 4], 0, () => ModelInvocationJobInputDataConfig$, () => ModelInvocationJobOutputDataConfig$, () => VpcConfig$, 1, () => TagList]
];
var CreateModelInvocationJobResponse$ = [
  3,
  n0,
  _CMIJRrea,
  0,
  [_jA],
  [0]
];
var CreatePromptRouterRequest$ = [
  3,
  n0,
  _CPRR,
  0,
  [_cRT, _pRN, _mo, _d, _rCo, _fM, _ta],
  [[0, 4], 0, () => PromptRouterTargetModels, [() => PromptRouterDescription, 0], () => RoutingCriteria$, () => PromptRouterTargetModel$, () => TagList]
];
var CreatePromptRouterResponse$ = [
  3,
  n0,
  _CPRRr,
  0,
  [_pRA],
  [0]
];
var CreateProvisionedModelThroughputRequest$ = [
  3,
  n0,
  _CPMTR,
  0,
  [_cRT, _mU, _pMN, _mIo, _cD, _ta],
  [[0, 4], 1, 0, 0, 0, () => TagList]
];
var CreateProvisionedModelThroughputResponse$ = [
  3,
  n0,
  _CPMTRr,
  0,
  [_pMA],
  [0]
];
var CustomMetricBedrockEvaluatorModel$ = [
  3,
  n0,
  _CMBEM,
  0,
  [_mI],
  [0]
];
var CustomMetricDefinition$ = [
  3,
  n0,
  _CMD,
  8,
  [_n, _in, _rS],
  [[() => MetricName, 0], 0, () => RatingScale]
];
var CustomMetricEvaluatorModelConfig$ = [
  3,
  n0,
  _CMEMC,
  0,
  [_bEM],
  [() => CustomMetricBedrockEvaluatorModels]
];
var CustomModelDeploymentSummary$ = [
  3,
  n0,
  _CMDS,
  0,
  [_cMDA, _cMDN, _mA, _cA, _s, _lUA, _fMa],
  [0, 0, 0, 5, 0, 5, 0]
];
var CustomModelDeploymentUpdateDetails$ = [
  3,
  n0,
  _CMDUD,
  0,
  [_mA, _uS],
  [0, 0]
];
var CustomModelSummary$ = [
  3,
  n0,
  _CMS,
  0,
  [_mA, _mN, _cTr, _bMA, _bMN, _cTu, _oAI, _mSo],
  [0, 0, 5, 0, 0, 0, 0, 0]
];
var CustomModelUnits$ = [
  3,
  n0,
  _CMU,
  0,
  [_cMUPMC, _cMUV],
  [1, 0]
];
var DataProcessingDetails$ = [
  3,
  n0,
  _DPD,
  0,
  [_s, _cTr, _lMT],
  [0, 5, 5]
];
var DeleteAutomatedReasoningPolicyBuildWorkflowRequest$ = [
  3,
  n0,
  _DARPBWR,
  0,
  [_pA, _bWI, _lUA],
  [[0, 1], [0, 1], [5, { [_hQ]: _uA }]]
];
var DeleteAutomatedReasoningPolicyBuildWorkflowResponse$ = [
  3,
  n0,
  _DARPBWRe,
  0,
  [],
  []
];
var DeleteAutomatedReasoningPolicyRequest$ = [
  3,
  n0,
  _DARPR,
  0,
  [_pA, _fo],
  [[0, 1], [2, { [_hQ]: _fo }]]
];
var DeleteAutomatedReasoningPolicyResponse$ = [
  3,
  n0,
  _DARPRe,
  0,
  [],
  []
];
var DeleteAutomatedReasoningPolicyTestCaseRequest$ = [
  3,
  n0,
  _DARPTCR,
  0,
  [_pA, _tCI, _lUA],
  [[0, 1], [0, 1], [5, { [_hQ]: _uA }]]
];
var DeleteAutomatedReasoningPolicyTestCaseResponse$ = [
  3,
  n0,
  _DARPTCRe,
  0,
  [],
  []
];
var DeleteCustomModelDeploymentRequest$ = [
  3,
  n0,
  _DCMDR,
  0,
  [_cMDI],
  [[0, 1]]
];
var DeleteCustomModelDeploymentResponse$ = [
  3,
  n0,
  _DCMDRe,
  0,
  [],
  []
];
var DeleteCustomModelRequest$ = [
  3,
  n0,
  _DCMR,
  0,
  [_mI],
  [[0, 1]]
];
var DeleteCustomModelResponse$ = [
  3,
  n0,
  _DCMRe,
  0,
  [],
  []
];
var DeleteEnforcedGuardrailConfigurationRequest$ = [
  3,
  n0,
  _DEGCR,
  0,
  [_cI],
  [[0, 1]]
];
var DeleteEnforcedGuardrailConfigurationResponse$ = [
  3,
  n0,
  _DEGCRe,
  0,
  [],
  []
];
var DeleteFoundationModelAgreementRequest$ = [
  3,
  n0,
  _DFMAR,
  0,
  [_mIo],
  [0]
];
var DeleteFoundationModelAgreementResponse$ = [
  3,
  n0,
  _DFMARe,
  0,
  [],
  []
];
var DeleteGuardrailRequest$ = [
  3,
  n0,
  _DGR,
  0,
  [_gI, _gV],
  [[0, 1], [0, { [_hQ]: _gV }]]
];
var DeleteGuardrailResponse$ = [
  3,
  n0,
  _DGRe,
  0,
  [],
  []
];
var DeleteImportedModelRequest$ = [
  3,
  n0,
  _DIMR,
  0,
  [_mI],
  [[0, 1]]
];
var DeleteImportedModelResponse$ = [
  3,
  n0,
  _DIMRe,
  0,
  [],
  []
];
var DeleteInferenceProfileRequest$ = [
  3,
  n0,
  _DIPR,
  0,
  [_iPI],
  [[0, 1]]
];
var DeleteInferenceProfileResponse$ = [
  3,
  n0,
  _DIPRe,
  0,
  [],
  []
];
var DeleteMarketplaceModelEndpointRequest$ = [
  3,
  n0,
  _DMMER,
  0,
  [_eA],
  [[0, 1]]
];
var DeleteMarketplaceModelEndpointResponse$ = [
  3,
  n0,
  _DMMERe,
  0,
  [],
  []
];
var DeleteModelInvocationLoggingConfigurationRequest$ = [
  3,
  n0,
  _DMILCR,
  0,
  [],
  []
];
var DeleteModelInvocationLoggingConfigurationResponse$ = [
  3,
  n0,
  _DMILCRe,
  0,
  [],
  []
];
var DeletePromptRouterRequest$ = [
  3,
  n0,
  _DPRR,
  0,
  [_pRA],
  [[0, 1]]
];
var DeletePromptRouterResponse$ = [
  3,
  n0,
  _DPRRe,
  0,
  [],
  []
];
var DeleteProvisionedModelThroughputRequest$ = [
  3,
  n0,
  _DPMTR,
  0,
  [_pMI],
  [[0, 1]]
];
var DeleteProvisionedModelThroughputResponse$ = [
  3,
  n0,
  _DPMTRe,
  0,
  [],
  []
];
var DeregisterMarketplaceModelEndpointRequest$ = [
  3,
  n0,
  _DMMERer,
  0,
  [_eA],
  [[0, 1]]
];
var DeregisterMarketplaceModelEndpointResponse$ = [
  3,
  n0,
  _DMMERere,
  0,
  [],
  []
];
var DimensionalPriceRate$ = [
  3,
  n0,
  _DPR,
  0,
  [_di, _pr, _d, _u],
  [0, 0, 0, 0]
];
var DistillationConfig$ = [
  3,
  n0,
  _DC,
  0,
  [_tMC],
  [() => TeacherModelConfig$]
];
var EvaluationBedrockModel$ = [
  3,
  n0,
  _EBM,
  0,
  [_mI, _iP, _pC],
  [0, [() => EvaluationModelInferenceParams, 0], () => PerformanceConfiguration$]
];
var EvaluationDataset$ = [
  3,
  n0,
  _ED,
  0,
  [_n, _dL],
  [[() => EvaluationDatasetName, 0], () => EvaluationDatasetLocation$]
];
var EvaluationDatasetMetricConfig$ = [
  3,
  n0,
  _EDMC,
  0,
  [_tT, _dat, _mNe],
  [0, [() => EvaluationDataset$, 0], [() => EvaluationMetricNames, 0]]
];
var EvaluationInferenceConfigSummary$ = [
  3,
  n0,
  _EICS,
  0,
  [_mCS, _rCS],
  [() => EvaluationModelConfigSummary$, () => EvaluationRagConfigSummary$]
];
var EvaluationModelConfigSummary$ = [
  3,
  n0,
  _EMCS,
  0,
  [_bMIe, _pISI],
  [64 | 0, 64 | 0]
];
var EvaluationOutputDataConfig$ = [
  3,
  n0,
  _EODC,
  0,
  [_sU],
  [0]
];
var EvaluationPrecomputedInferenceSource$ = [
  3,
  n0,
  _EPIS,
  0,
  [_iSI],
  [0]
];
var EvaluationPrecomputedRetrieveAndGenerateSourceConfig$ = [
  3,
  n0,
  _EPRAGSC,
  0,
  [_rSI],
  [0]
];
var EvaluationPrecomputedRetrieveSourceConfig$ = [
  3,
  n0,
  _EPRSC,
  0,
  [_rSI],
  [0]
];
var EvaluationRagConfigSummary$ = [
  3,
  n0,
  _ERCS,
  0,
  [_bKBI, _pRSI],
  [64 | 0, 64 | 0]
];
var EvaluationSummary$ = [
  3,
  n0,
  _ES,
  0,
  [_jA, _jN, _s, _cTr, _jTo, _eTT, _mIod, _rIa, _eMI, _cMEMI, _iCS, _aT],
  [0, 0, 0, 5, 0, 64 | 0, 64 | 0, 64 | 0, 64 | 0, 64 | 0, () => EvaluationInferenceConfigSummary$, 0]
];
var ExportAutomatedReasoningPolicyVersionRequest$ = [
  3,
  n0,
  _EARPVR,
  0,
  [_pA],
  [[0, 1]]
];
var ExportAutomatedReasoningPolicyVersionResponse$ = [
  3,
  n0,
  _EARPVRx,
  0,
  [_pD],
  [[() => AutomatedReasoningPolicyDefinition$, 16]]
];
var ExternalSource$ = [
  3,
  n0,
  _ESx,
  0,
  [_sT, _sL, _bC],
  [0, () => S3ObjectDoc$, [() => ByteContentDoc$, 0]]
];
var ExternalSourcesGenerationConfiguration$ = [
  3,
  n0,
  _ESGC,
  0,
  [_pT, _gCu, _kIC, _aMRF],
  [[() => PromptTemplate$, 0], () => GuardrailConfiguration$, () => KbInferenceConfig$, 128 | 15]
];
var ExternalSourcesRetrieveAndGenerateConfiguration$ = [
  3,
  n0,
  _ESRAGC,
  0,
  [_mA, _so, _gCe],
  [0, [() => ExternalSources, 0], [() => ExternalSourcesGenerationConfiguration$, 0]]
];
var FieldForReranking$ = [
  3,
  n0,
  _FFR,
  0,
  [_fN],
  [0]
];
var FilterAttribute$ = [
  3,
  n0,
  _FA,
  0,
  [_k, _va],
  [0, 15]
];
var FoundationModelDetails$ = [
  3,
  n0,
  _FMD,
  0,
  [_mA, _mIo, _mN, _pN, _iM, _oM, _rSS, _cS, _iTS, _mL],
  [0, 0, 0, 0, 64 | 0, 64 | 0, 2, 64 | 0, 64 | 0, () => FoundationModelLifecycle$]
];
var FoundationModelLifecycle$ = [
  3,
  n0,
  _FML,
  0,
  [_s],
  [0]
];
var FoundationModelSummary$ = [
  3,
  n0,
  _FMS,
  0,
  [_mA, _mIo, _mN, _pN, _iM, _oM, _rSS, _cS, _iTS, _mL],
  [0, 0, 0, 0, 64 | 0, 64 | 0, 2, 64 | 0, 64 | 0, () => FoundationModelLifecycle$]
];
var GenerationConfiguration$ = [
  3,
  n0,
  _GC,
  0,
  [_pT, _gCu, _kIC, _aMRF],
  [[() => PromptTemplate$, 0], () => GuardrailConfiguration$, () => KbInferenceConfig$, 128 | 15]
];
var GetAutomatedReasoningPolicyAnnotationsRequest$ = [
  3,
  n0,
  _GARPAR,
  0,
  [_pA, _bWI],
  [[0, 1], [0, 1]]
];
var GetAutomatedReasoningPolicyAnnotationsResponse$ = [
  3,
  n0,
  _GARPARe,
  0,
  [_pA, _n, _bWI, _an, _aSH, _uA],
  [0, [() => AutomatedReasoningPolicyName, 0], 0, [() => AutomatedReasoningPolicyAnnotationList, 0], 0, 5]
];
var GetAutomatedReasoningPolicyBuildWorkflowRequest$ = [
  3,
  n0,
  _GARPBWR,
  0,
  [_pA, _bWI],
  [[0, 1], [0, 1]]
];
var GetAutomatedReasoningPolicyBuildWorkflowResponse$ = [
  3,
  n0,
  _GARPBWRe,
  0,
  [_pA, _bWI, _s, _bWT, _dN, _dCT, _dD, _cA, _uA],
  [0, 0, 0, 0, [() => AutomatedReasoningPolicyBuildDocumentName, 0], 0, [() => AutomatedReasoningPolicyBuildDocumentDescription, 0], 5, 5]
];
var GetAutomatedReasoningPolicyBuildWorkflowResultAssetsRequest$ = [
  3,
  n0,
  _GARPBWRAR,
  0,
  [_pA, _bWI, _aTs],
  [[0, 1], [0, 1], [0, { [_hQ]: _aTs }]]
];
var GetAutomatedReasoningPolicyBuildWorkflowResultAssetsResponse$ = [
  3,
  n0,
  _GARPBWRARe,
  0,
  [_pA, _bWI, _bWA],
  [0, 0, [() => AutomatedReasoningPolicyBuildResultAssets$, 0]]
];
var GetAutomatedReasoningPolicyNextScenarioRequest$ = [
  3,
  n0,
  _GARPNSR,
  0,
  [_pA, _bWI],
  [[0, 1], [0, 1]]
];
var GetAutomatedReasoningPolicyNextScenarioResponse$ = [
  3,
  n0,
  _GARPNSRe,
  0,
  [_pA, _sc],
  [0, [() => AutomatedReasoningPolicyScenario$, 0]]
];
var GetAutomatedReasoningPolicyRequest$ = [
  3,
  n0,
  _GARPR,
  0,
  [_pA],
  [[0, 1]]
];
var GetAutomatedReasoningPolicyResponse$ = [
  3,
  n0,
  _GARPRe,
  0,
  [_pA, _n, _ve, _pI, _d, _dH, _kKA, _cA, _uA],
  [0, [() => AutomatedReasoningPolicyName, 0], 0, 0, [() => AutomatedReasoningPolicyDescription, 0], 0, 0, 5, 5]
];
var GetAutomatedReasoningPolicyTestCaseRequest$ = [
  3,
  n0,
  _GARPTCR,
  0,
  [_pA, _tCI],
  [[0, 1], [0, 1]]
];
var GetAutomatedReasoningPolicyTestCaseResponse$ = [
  3,
  n0,
  _GARPTCRe,
  0,
  [_pA, _tCe],
  [0, [() => AutomatedReasoningPolicyTestCase$, 0]]
];
var GetAutomatedReasoningPolicyTestResultRequest$ = [
  3,
  n0,
  _GARPTRR,
  0,
  [_pA, _bWI, _tCI],
  [[0, 1], [0, 1], [0, 1]]
];
var GetAutomatedReasoningPolicyTestResultResponse$ = [
  3,
  n0,
  _GARPTRRe,
  0,
  [_tR],
  [[() => AutomatedReasoningPolicyTestResult$, 0]]
];
var GetCustomModelDeploymentRequest$ = [
  3,
  n0,
  _GCMDR,
  0,
  [_cMDI],
  [[0, 1]]
];
var GetCustomModelDeploymentResponse$ = [
  3,
  n0,
  _GCMDRe,
  0,
  [_cMDA, _mDN, _mA, _cA, _s, _d, _uD, _fMa, _lUA],
  [0, 0, 0, 5, 0, 0, () => CustomModelDeploymentUpdateDetails$, 0, 5]
];
var GetCustomModelRequest$ = [
  3,
  n0,
  _GCMR,
  0,
  [_mI],
  [[0, 1]]
];
var GetCustomModelResponse$ = [
  3,
  n0,
  _GCMRe,
  0,
  [_mA, _mN, _jN, _jA, _bMA, _cTu, _mKKA, _hP, _tDC, _vDC, _oDC, _tM, _vM, _cTr, _cC, _mSo, _fMa],
  [0, 0, 0, 0, 0, 0, 0, 128 | 0, [() => TrainingDataConfig$, 0], () => ValidationDataConfig$, () => OutputDataConfig$, () => TrainingMetrics$, () => ValidationMetrics, 5, () => CustomizationConfig$, 0, 0]
];
var GetEvaluationJobRequest$ = [
  3,
  n0,
  _GEJR,
  0,
  [_jI],
  [[() => EvaluationJobIdentifier, 1]]
];
var GetEvaluationJobResponse$ = [
  3,
  n0,
  _GEJRe,
  0,
  [_jN, _s, _jA, _jD, _rA, _cEKI, _jTo, _aT, _eC, _iC, _oDC, _cTr, _lMT, _fMai],
  [0, 0, 0, [() => EvaluationJobDescription, 0], 0, 0, 0, 0, [() => EvaluationConfig$, 0], [() => EvaluationInferenceConfig$, 0], () => EvaluationOutputDataConfig$, 5, 5, 64 | 0]
];
var GetFoundationModelAvailabilityRequest$ = [
  3,
  n0,
  _GFMAR,
  0,
  [_mIo],
  [[0, 1]]
];
var GetFoundationModelAvailabilityResponse$ = [
  3,
  n0,
  _GFMARe,
  0,
  [_mIo, _aA, _aS, _eAn, _rAe],
  [0, () => AgreementAvailability$, 0, 0, 0]
];
var GetFoundationModelRequest$ = [
  3,
  n0,
  _GFMR,
  0,
  [_mI],
  [[0, 1]]
];
var GetFoundationModelResponse$ = [
  3,
  n0,
  _GFMRe,
  0,
  [_mD],
  [() => FoundationModelDetails$]
];
var GetGuardrailRequest$ = [
  3,
  n0,
  _GGR,
  0,
  [_gI, _gV],
  [[0, 1], [0, { [_hQ]: _gV }]]
];
var GetGuardrailResponse$ = [
  3,
  n0,
  _GGRe,
  0,
  [_n, _d, _gIu, _gA, _ve, _s, _tP, _cP, _wP, _sIP, _cGP, _aRP, _cRD, _cA, _uA, _sRt, _fR, _bIM, _bOM, _kKA],
  [[() => GuardrailName, 0], [() => GuardrailDescription, 0], 0, 0, 0, 0, [() => GuardrailTopicPolicy$, 0], [() => GuardrailContentPolicy$, 0], [() => GuardrailWordPolicy$, 0], () => GuardrailSensitiveInformationPolicy$, [() => GuardrailContextualGroundingPolicy$, 0], () => GuardrailAutomatedReasoningPolicy$, () => GuardrailCrossRegionDetails$, 5, 5, [() => GuardrailStatusReasons, 0], [() => GuardrailFailureRecommendations, 0], [() => GuardrailBlockedMessaging, 0], [() => GuardrailBlockedMessaging, 0], 0]
];
var GetImportedModelRequest$ = [
  3,
  n0,
  _GIMR,
  0,
  [_mI],
  [[0, 1]]
];
var GetImportedModelResponse$ = [
  3,
  n0,
  _GIMRe,
  0,
  [_mA, _mN, _jN, _jA, _mDS, _cTr, _mAo, _mKKA, _iS, _cMU],
  [0, 0, 0, 0, () => ModelDataSource$, 5, 0, 0, 2, () => CustomModelUnits$]
];
var GetInferenceProfileRequest$ = [
  3,
  n0,
  _GIPR,
  0,
  [_iPI],
  [[0, 1]]
];
var GetInferenceProfileResponse$ = [
  3,
  n0,
  _GIPRe,
  0,
  [_iPN, _d, _cA, _uA, _iPA, _mo, _iPIn, _s, _ty],
  [0, [() => InferenceProfileDescription, 0], 5, 5, 0, () => InferenceProfileModels, 0, 0, 0]
];
var GetMarketplaceModelEndpointRequest$ = [
  3,
  n0,
  _GMMER,
  0,
  [_eA],
  [[0, 1]]
];
var GetMarketplaceModelEndpointResponse$ = [
  3,
  n0,
  _GMMERe,
  0,
  [_mME],
  [() => MarketplaceModelEndpoint$]
];
var GetModelCopyJobRequest$ = [
  3,
  n0,
  _GMCJR,
  0,
  [_jA],
  [[0, 1]]
];
var GetModelCopyJobResponse$ = [
  3,
  n0,
  _GMCJRe,
  0,
  [_jA, _s, _cTr, _tMA, _tMN, _sAI, _sMA, _tMKKA, _tMT, _fMa, _sMN],
  [0, 0, 5, 0, 0, 0, 0, 0, () => TagList, 0, 0]
];
var GetModelCustomizationJobRequest$ = [
  3,
  n0,
  _GMCJRet,
  0,
  [_jI],
  [[0, 1]]
];
var GetModelCustomizationJobResponse$ = [
  3,
  n0,
  _GMCJReto,
  0,
  [_jA, _jN, _oMN, _oMA, _cRT, _rA, _s, _sD, _fMa, _cTr, _lMT, _eT, _bMA, _hP, _tDC, _vDC, _oDC, _cTu, _oMKKA, _tM, _vM, _vCp, _cC],
  [0, 0, 0, 0, 0, 0, 0, () => StatusDetails$, 0, 5, 5, 5, 0, 128 | 0, [() => TrainingDataConfig$, 0], () => ValidationDataConfig$, () => OutputDataConfig$, 0, 0, () => TrainingMetrics$, () => ValidationMetrics, () => VpcConfig$, () => CustomizationConfig$]
];
var GetModelImportJobRequest$ = [
  3,
  n0,
  _GMIJR,
  0,
  [_jI],
  [[0, 1]]
];
var GetModelImportJobResponse$ = [
  3,
  n0,
  _GMIJRe,
  0,
  [_jA, _jN, _iMN, _iMA, _rA, _mDS, _s, _fMa, _cTr, _lMT, _eT, _vCp, _iMKKA],
  [0, 0, 0, 0, 0, () => ModelDataSource$, 0, 0, 5, 5, 5, () => VpcConfig$, 0]
];
var GetModelInvocationJobRequest$ = [
  3,
  n0,
  _GMIJRet,
  0,
  [_jI],
  [[0, 1]]
];
var GetModelInvocationJobResponse$ = [
  3,
  n0,
  _GMIJReto,
  0,
  [_jA, _jN, _mIo, _cRT, _rA, _s, _m, _sTu, _lMT, _eT, _iDC, _oDC, _vCp, _tDIH, _jET],
  [0, 0, 0, 0, 0, 0, [() => Message, 0], 5, 5, 5, () => ModelInvocationJobInputDataConfig$, () => ModelInvocationJobOutputDataConfig$, () => VpcConfig$, 1, 5]
];
var GetModelInvocationLoggingConfigurationRequest$ = [
  3,
  n0,
  _GMILCR,
  0,
  [],
  []
];
var GetModelInvocationLoggingConfigurationResponse$ = [
  3,
  n0,
  _GMILCRe,
  0,
  [_lC],
  [() => LoggingConfig$]
];
var GetPromptRouterRequest$ = [
  3,
  n0,
  _GPRR,
  0,
  [_pRA],
  [[0, 1]]
];
var GetPromptRouterResponse$ = [
  3,
  n0,
  _GPRRe,
  0,
  [_pRN, _rCo, _d, _cA, _uA, _pRA, _mo, _fM, _s, _ty],
  [0, () => RoutingCriteria$, [() => PromptRouterDescription, 0], 5, 5, 0, () => PromptRouterTargetModels, () => PromptRouterTargetModel$, 0, 0]
];
var GetProvisionedModelThroughputRequest$ = [
  3,
  n0,
  _GPMTR,
  0,
  [_pMI],
  [[0, 1]]
];
var GetProvisionedModelThroughputResponse$ = [
  3,
  n0,
  _GPMTRe,
  0,
  [_mU, _dMU, _pMN, _pMA, _mA, _dMA, _fMA, _s, _cTr, _lMT, _fMa, _cD, _cET],
  [1, 1, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 5]
];
var GetUseCaseForModelAccessRequest$ = [
  3,
  n0,
  _GUCFMAR,
  0,
  [],
  []
];
var GetUseCaseForModelAccessResponse$ = [
  3,
  n0,
  _GUCFMARe,
  0,
  [_fD],
  [21]
];
var GuardrailAutomatedReasoningPolicy$ = [
  3,
  n0,
  _GARP,
  0,
  [_po, _cT],
  [64 | 0, 1]
];
var GuardrailAutomatedReasoningPolicyConfig$ = [
  3,
  n0,
  _GARPC,
  0,
  [_po, _cT],
  [64 | 0, 1]
];
var GuardrailConfiguration$ = [
  3,
  n0,
  _GCu,
  0,
  [_gIu, _gV],
  [0, 0]
];
var GuardrailContentFilter$ = [
  3,
  n0,
  _GCF,
  0,
  [_ty, _iSn, _oS, _iM, _oM, _iA, _oA, _iE, _oE],
  [0, 0, 0, [() => GuardrailModalities, 0], [() => GuardrailModalities, 0], [() => GuardrailContentFilterAction, 0], [() => GuardrailContentFilterAction, 0], 2, 2]
];
var GuardrailContentFilterConfig$ = [
  3,
  n0,
  _GCFC,
  0,
  [_ty, _iSn, _oS, _iM, _oM, _iA, _oA, _iE, _oE],
  [0, 0, 0, [() => GuardrailModalities, 0], [() => GuardrailModalities, 0], [() => GuardrailContentFilterAction, 0], [() => GuardrailContentFilterAction, 0], 2, 2]
];
var GuardrailContentFiltersTier$ = [
  3,
  n0,
  _GCFT,
  0,
  [_tNi],
  [[() => GuardrailContentFiltersTierName, 0]]
];
var GuardrailContentFiltersTierConfig$ = [
  3,
  n0,
  _GCFTC,
  0,
  [_tNi],
  [[() => GuardrailContentFiltersTierName, 0]]
];
var GuardrailContentPolicy$ = [
  3,
  n0,
  _GCP,
  0,
  [_fi, _ti],
  [[() => GuardrailContentFilters, 0], [() => GuardrailContentFiltersTier$, 0]]
];
var GuardrailContentPolicyConfig$ = [
  3,
  n0,
  _GCPC,
  0,
  [_fC, _tCi],
  [[() => GuardrailContentFiltersConfig, 0], [() => GuardrailContentFiltersTierConfig$, 0]]
];
var GuardrailContextualGroundingFilter$ = [
  3,
  n0,
  _GCGF,
  0,
  [_ty, _th, _ac, _ena],
  [0, 1, [() => GuardrailContextualGroundingAction, 0], 2]
];
var GuardrailContextualGroundingFilterConfig$ = [
  3,
  n0,
  _GCGFC,
  0,
  [_ty, _th, _ac, _ena],
  [0, 1, [() => GuardrailContextualGroundingAction, 0], 2]
];
var GuardrailContextualGroundingPolicy$ = [
  3,
  n0,
  _GCGP,
  0,
  [_fi],
  [[() => GuardrailContextualGroundingFilters, 0]]
];
var GuardrailContextualGroundingPolicyConfig$ = [
  3,
  n0,
  _GCGPC,
  0,
  [_fC],
  [[() => GuardrailContextualGroundingFiltersConfig, 0]]
];
var GuardrailCrossRegionConfig$ = [
  3,
  n0,
  _GCRC,
  0,
  [_gPI],
  [0]
];
var GuardrailCrossRegionDetails$ = [
  3,
  n0,
  _GCRD,
  0,
  [_gPIu, _gPA],
  [0, 0]
];
var GuardrailManagedWords$ = [
  3,
  n0,
  _GMW,
  0,
  [_ty, _iA, _oA, _iE, _oE],
  [0, [() => GuardrailWordAction, 0], [() => GuardrailWordAction, 0], 2, 2]
];
var GuardrailManagedWordsConfig$ = [
  3,
  n0,
  _GMWC,
  0,
  [_ty, _iA, _oA, _iE, _oE],
  [0, [() => GuardrailWordAction, 0], [() => GuardrailWordAction, 0], 2, 2]
];
var GuardrailPiiEntity$ = [
  3,
  n0,
  _GPE,
  0,
  [_ty, _ac, _iA, _oA, _iE, _oE],
  [0, 0, 0, 0, 2, 2]
];
var GuardrailPiiEntityConfig$ = [
  3,
  n0,
  _GPEC,
  0,
  [_ty, _ac, _iA, _oA, _iE, _oE],
  [0, 0, 0, 0, 2, 2]
];
var GuardrailRegex$ = [
  3,
  n0,
  _GR,
  0,
  [_n, _d, _pa, _ac, _iA, _oA, _iE, _oE],
  [0, 0, 0, 0, 0, 0, 2, 2]
];
var GuardrailRegexConfig$ = [
  3,
  n0,
  _GRC,
  0,
  [_n, _d, _pa, _ac, _iA, _oA, _iE, _oE],
  [0, 0, 0, 0, 0, 0, 2, 2]
];
var GuardrailSensitiveInformationPolicy$ = [
  3,
  n0,
  _GSIP,
  0,
  [_pEi, _re],
  [() => GuardrailPiiEntities, () => GuardrailRegexes]
];
var GuardrailSensitiveInformationPolicyConfig$ = [
  3,
  n0,
  _GSIPC,
  0,
  [_pEC, _rCe],
  [() => GuardrailPiiEntitiesConfig, () => GuardrailRegexesConfig]
];
var GuardrailSummary$ = [
  3,
  n0,
  _GS,
  0,
  [_i, _ar, _s, _n, _d, _ve, _cA, _uA, _cRD],
  [0, 0, 0, [() => GuardrailName, 0], [() => GuardrailDescription, 0], 0, 5, 5, () => GuardrailCrossRegionDetails$]
];
var GuardrailTopic$ = [
  3,
  n0,
  _GT,
  0,
  [_n, _de, _exa, _ty, _iA, _oA, _iE, _oE],
  [[() => GuardrailTopicName, 0], [() => GuardrailTopicDefinition, 0], [() => GuardrailTopicExamples, 0], 0, [() => GuardrailTopicAction, 0], [() => GuardrailTopicAction, 0], 2, 2]
];
var GuardrailTopicConfig$ = [
  3,
  n0,
  _GTC,
  0,
  [_n, _de, _exa, _ty, _iA, _oA, _iE, _oE],
  [[() => GuardrailTopicName, 0], [() => GuardrailTopicDefinition, 0], [() => GuardrailTopicExamples, 0], 0, [() => GuardrailTopicAction, 0], [() => GuardrailTopicAction, 0], 2, 2]
];
var GuardrailTopicPolicy$ = [
  3,
  n0,
  _GTP,
  0,
  [_to, _ti],
  [[() => GuardrailTopics, 0], [() => GuardrailTopicsTier$, 0]]
];
var GuardrailTopicPolicyConfig$ = [
  3,
  n0,
  _GTPC,
  0,
  [_tCo, _tCi],
  [[() => GuardrailTopicsConfig, 0], [() => GuardrailTopicsTierConfig$, 0]]
];
var GuardrailTopicsTier$ = [
  3,
  n0,
  _GTT,
  0,
  [_tNi],
  [[() => GuardrailTopicsTierName, 0]]
];
var GuardrailTopicsTierConfig$ = [
  3,
  n0,
  _GTTC,
  0,
  [_tNi],
  [[() => GuardrailTopicsTierName, 0]]
];
var GuardrailWord$ = [
  3,
  n0,
  _GW,
  0,
  [_te, _iA, _oA, _iE, _oE],
  [0, [() => GuardrailWordAction, 0], [() => GuardrailWordAction, 0], 2, 2]
];
var GuardrailWordConfig$ = [
  3,
  n0,
  _GWC,
  0,
  [_te, _iA, _oA, _iE, _oE],
  [0, [() => GuardrailWordAction, 0], [() => GuardrailWordAction, 0], 2, 2]
];
var GuardrailWordPolicy$ = [
  3,
  n0,
  _GWP,
  0,
  [_w, _mWL],
  [[() => GuardrailWords, 0], [() => GuardrailManagedWordLists, 0]]
];
var GuardrailWordPolicyConfig$ = [
  3,
  n0,
  _GWPC,
  0,
  [_wCo, _mWLC],
  [[() => GuardrailWordsConfig, 0], [() => GuardrailManagedWordListsConfig, 0]]
];
var HumanEvaluationConfig$ = [
  3,
  n0,
  _HEC,
  0,
  [_hWC, _cM, _dMC],
  [[() => HumanWorkflowConfig$, 0], [() => HumanEvaluationCustomMetrics, 0], [() => EvaluationDatasetMetricConfigs, 0]]
];
var HumanEvaluationCustomMetric$ = [
  3,
  n0,
  _HECM,
  0,
  [_n, _d, _rM],
  [[() => EvaluationMetricName, 0], [() => EvaluationMetricDescription, 0], 0]
];
var HumanWorkflowConfig$ = [
  3,
  n0,
  _HWC,
  0,
  [_fDA, _in],
  [0, [() => HumanTaskInstructions, 0]]
];
var ImplicitFilterConfiguration$ = [
  3,
  n0,
  _IFC,
  0,
  [_mAe, _mA],
  [[() => MetadataAttributeSchemaList, 0], 0]
];
var ImportedModelSummary$ = [
  3,
  n0,
  _IMS,
  0,
  [_mA, _mN, _cTr, _iS, _mAo],
  [0, 0, 5, 2, 0]
];
var InferenceProfileModel$ = [
  3,
  n0,
  _IPM,
  0,
  [_mA],
  [0]
];
var InferenceProfileSummary$ = [
  3,
  n0,
  _IPS,
  0,
  [_iPN, _d, _cA, _uA, _iPA, _mo, _iPIn, _s, _ty],
  [0, [() => InferenceProfileDescription, 0], 5, 5, 0, () => InferenceProfileModels, 0, 0, 0]
];
var InternalServerException$ = [
  -3,
  n0,
  _ISE,
  { [_e]: _se, [_hE]: 500 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(InternalServerException$, InternalServerException);
var InvocationLogsConfig$ = [
  3,
  n0,
  _ILC,
  0,
  [_uPR, _iLS, _rMF],
  [2, () => InvocationLogSource$, [() => RequestMetadataFilters$, 0]]
];
var KbInferenceConfig$ = [
  3,
  n0,
  _KIC,
  0,
  [_tIC],
  [() => TextInferenceConfig$]
];
var KnowledgeBaseRetrievalConfiguration$ = [
  3,
  n0,
  _KBRC,
  0,
  [_vSC],
  [[() => KnowledgeBaseVectorSearchConfiguration$, 0]]
];
var KnowledgeBaseRetrieveAndGenerateConfiguration$ = [
  3,
  n0,
  _KBRAGC,
  0,
  [_kBI, _mA, _rCet, _gCe, _oC],
  [0, 0, [() => KnowledgeBaseRetrievalConfiguration$, 0], [() => GenerationConfiguration$, 0], () => OrchestrationConfiguration$]
];
var KnowledgeBaseVectorSearchConfiguration$ = [
  3,
  n0,
  _KBVSC,
  0,
  [_nOR, _oST, _fil, _iFC, _rCer],
  [1, 0, [() => RetrievalFilter$, 0], [() => ImplicitFilterConfiguration$, 0], [() => VectorSearchRerankingConfiguration$, 0]]
];
var LambdaGraderConfig$ = [
  3,
  n0,
  _LGC,
  0,
  [_lA],
  [0]
];
var LegalTerm$ = [
  3,
  n0,
  _LT,
  0,
  [_ur],
  [0]
];
var ListAutomatedReasoningPoliciesRequest$ = [
  3,
  n0,
  _LARPR,
  0,
  [_pA, _nT, _mR],
  [[0, { [_hQ]: _pA }], [0, { [_hQ]: _nT }], [1, { [_hQ]: _mR }]]
];
var ListAutomatedReasoningPoliciesResponse$ = [
  3,
  n0,
  _LARPRi,
  0,
  [_aRPS, _nT],
  [[() => AutomatedReasoningPolicySummaries, 0], 0]
];
var ListAutomatedReasoningPolicyBuildWorkflowsRequest$ = [
  3,
  n0,
  _LARPBWR,
  0,
  [_pA, _nT, _mR],
  [[0, 1], [0, { [_hQ]: _nT }], [1, { [_hQ]: _mR }]]
];
var ListAutomatedReasoningPolicyBuildWorkflowsResponse$ = [
  3,
  n0,
  _LARPBWRi,
  0,
  [_aRPBWS, _nT],
  [() => AutomatedReasoningPolicyBuildWorkflowSummaries, 0]
];
var ListAutomatedReasoningPolicyTestCasesRequest$ = [
  3,
  n0,
  _LARPTCR,
  0,
  [_pA, _nT, _mR],
  [[0, 1], [0, { [_hQ]: _nT }], [1, { [_hQ]: _mR }]]
];
var ListAutomatedReasoningPolicyTestCasesResponse$ = [
  3,
  n0,
  _LARPTCRi,
  0,
  [_tCes, _nT],
  [[() => AutomatedReasoningPolicyTestCaseList, 0], 0]
];
var ListAutomatedReasoningPolicyTestResultsRequest$ = [
  3,
  n0,
  _LARPTRR,
  0,
  [_pA, _bWI, _nT, _mR],
  [[0, 1], [0, 1], [0, { [_hQ]: _nT }], [1, { [_hQ]: _mR }]]
];
var ListAutomatedReasoningPolicyTestResultsResponse$ = [
  3,
  n0,
  _LARPTRRi,
  0,
  [_tRe, _nT],
  [[() => AutomatedReasoningPolicyTestList, 0], 0]
];
var ListCustomModelDeploymentsRequest$ = [
  3,
  n0,
  _LCMDR,
  0,
  [_cBr, _cAr, _nC, _mR, _nT, _sB, _sO, _sEt, _mAE],
  [[5, { [_hQ]: _cBr }], [5, { [_hQ]: _cAr }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _mAE }]]
];
var ListCustomModelDeploymentsResponse$ = [
  3,
  n0,
  _LCMDRi,
  0,
  [_nT, _mDSo],
  [0, () => CustomModelDeploymentSummaryList]
];
var ListCustomModelsRequest$ = [
  3,
  n0,
  _LCMR,
  0,
  [_cTB, _cTA, _nC, _bMAE, _fMAE, _mR, _nT, _sB, _sO, _iO, _mSo],
  [[5, { [_hQ]: _cTB }], [5, { [_hQ]: _cTA }], [0, { [_hQ]: _nC }], [0, { [_hQ]: _bMAE }], [0, { [_hQ]: _fMAE }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }], [2, { [_hQ]: _iO }], [0, { [_hQ]: _mSo }]]
];
var ListCustomModelsResponse$ = [
  3,
  n0,
  _LCMRi,
  0,
  [_nT, _mSod],
  [0, () => CustomModelSummaryList]
];
var ListEnforcedGuardrailsConfigurationRequest$ = [
  3,
  n0,
  _LEGCR,
  0,
  [_nT],
  [[0, { [_hQ]: _nT }]]
];
var ListEnforcedGuardrailsConfigurationResponse$ = [
  3,
  n0,
  _LEGCRi,
  0,
  [_gCua, _nT],
  [() => AccountEnforcedGuardrailsOutputConfiguration, 0]
];
var ListEvaluationJobsRequest$ = [
  3,
  n0,
  _LEJR,
  0,
  [_cTA, _cTB, _sEt, _aTE, _nC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _cTA }], [5, { [_hQ]: _cTB }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _aTE }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListEvaluationJobsResponse$ = [
  3,
  n0,
  _LEJRi,
  0,
  [_nT, _jSo],
  [0, () => EvaluationSummaries]
];
var ListFoundationModelAgreementOffersRequest$ = [
  3,
  n0,
  _LFMAOR,
  0,
  [_mIo, _oTf],
  [[0, 1], [0, { [_hQ]: _oTf }]]
];
var ListFoundationModelAgreementOffersResponse$ = [
  3,
  n0,
  _LFMAORi,
  0,
  [_mIo, _of],
  [0, () => Offers]
];
var ListFoundationModelsRequest$ = [
  3,
  n0,
  _LFMR,
  0,
  [_bP, _bCT, _bOMy, _bIT],
  [[0, { [_hQ]: _bP }], [0, { [_hQ]: _bCT }], [0, { [_hQ]: _bOMy }], [0, { [_hQ]: _bIT }]]
];
var ListFoundationModelsResponse$ = [
  3,
  n0,
  _LFMRi,
  0,
  [_mSod],
  [() => FoundationModelSummaryList]
];
var ListGuardrailsRequest$ = [
  3,
  n0,
  _LGR,
  0,
  [_gI, _mR, _nT],
  [[0, { [_hQ]: _gI }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }]]
];
var ListGuardrailsResponse$ = [
  3,
  n0,
  _LGRi,
  0,
  [_g, _nT],
  [[() => GuardrailSummaries, 0], 0]
];
var ListImportedModelsRequest$ = [
  3,
  n0,
  _LIMR,
  0,
  [_cTB, _cTA, _nC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _cTB }], [5, { [_hQ]: _cTA }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListImportedModelsResponse$ = [
  3,
  n0,
  _LIMRi,
  0,
  [_nT, _mSod],
  [0, () => ImportedModelSummaryList]
];
var ListInferenceProfilesRequest$ = [
  3,
  n0,
  _LIPR,
  0,
  [_mR, _nT, _tE],
  [[1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _ty }]]
];
var ListInferenceProfilesResponse$ = [
  3,
  n0,
  _LIPRi,
  0,
  [_iPS, _nT],
  [[() => InferenceProfileSummaries, 0], 0]
];
var ListMarketplaceModelEndpointsRequest$ = [
  3,
  n0,
  _LMMER,
  0,
  [_mR, _nT, _mSE],
  [[1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _mSI }]]
];
var ListMarketplaceModelEndpointsResponse$ = [
  3,
  n0,
  _LMMERi,
  0,
  [_mMEa, _nT],
  [() => MarketplaceModelEndpointSummaries, 0]
];
var ListModelCopyJobsRequest$ = [
  3,
  n0,
  _LMCJR,
  0,
  [_cTA, _cTB, _sEt, _sAE, _sMAE, _tMNC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _cTA }], [5, { [_hQ]: _cTB }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _sAE }], [0, { [_hQ]: _sMAE }], [0, { [_hQ]: _oMNC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListModelCopyJobsResponse$ = [
  3,
  n0,
  _LMCJRi,
  0,
  [_nT, _mCJS],
  [0, () => ModelCopyJobSummaries]
];
var ListModelCustomizationJobsRequest$ = [
  3,
  n0,
  _LMCJRis,
  0,
  [_cTA, _cTB, _sEt, _nC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _cTA }], [5, { [_hQ]: _cTB }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListModelCustomizationJobsResponse$ = [
  3,
  n0,
  _LMCJRist,
  0,
  [_nT, _mCJSo],
  [0, () => ModelCustomizationJobSummaries]
];
var ListModelImportJobsRequest$ = [
  3,
  n0,
  _LMIJR,
  0,
  [_cTA, _cTB, _sEt, _nC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _cTA }], [5, { [_hQ]: _cTB }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListModelImportJobsResponse$ = [
  3,
  n0,
  _LMIJRi,
  0,
  [_nT, _mIJS],
  [0, () => ModelImportJobSummaries]
];
var ListModelInvocationJobsRequest$ = [
  3,
  n0,
  _LMIJRis,
  0,
  [_sTA, _sTB, _sEt, _nC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _sTA }], [5, { [_hQ]: _sTB }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListModelInvocationJobsResponse$ = [
  3,
  n0,
  _LMIJRist,
  0,
  [_nT, _iJS],
  [0, [() => ModelInvocationJobSummaries, 0]]
];
var ListPromptRoutersRequest$ = [
  3,
  n0,
  _LPRR,
  0,
  [_mR, _nT, _ty],
  [[1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _ty }]]
];
var ListPromptRoutersResponse$ = [
  3,
  n0,
  _LPRRi,
  0,
  [_pRS, _nT],
  [[() => PromptRouterSummaries, 0], 0]
];
var ListProvisionedModelThroughputsRequest$ = [
  3,
  n0,
  _LPMTR,
  0,
  [_cTA, _cTB, _sEt, _mAE, _nC, _mR, _nT, _sB, _sO],
  [[5, { [_hQ]: _cTA }], [5, { [_hQ]: _cTB }], [0, { [_hQ]: _sEt }], [0, { [_hQ]: _mAE }], [0, { [_hQ]: _nC }], [1, { [_hQ]: _mR }], [0, { [_hQ]: _nT }], [0, { [_hQ]: _sB }], [0, { [_hQ]: _sO }]]
];
var ListProvisionedModelThroughputsResponse$ = [
  3,
  n0,
  _LPMTRi,
  0,
  [_nT, _pMS],
  [0, () => ProvisionedModelSummaries]
];
var ListTagsForResourceRequest$ = [
  3,
  n0,
  _LTFRR,
  0,
  [_rARN],
  [0]
];
var ListTagsForResourceResponse$ = [
  3,
  n0,
  _LTFRRi,
  0,
  [_ta],
  [() => TagList]
];
var LoggingConfig$ = [
  3,
  n0,
  _LC,
  0,
  [_cWC, _sC, _tDDE, _iDDE, _eDDE, _vDDE, _aDDE],
  [() => CloudWatchConfig$, () => S3Config$, 2, 2, 2, 2, 2]
];
var MarketplaceModelEndpoint$ = [
  3,
  n0,
  _MME,
  0,
  [_eA, _mSI, _s, _sM, _cA, _uA, _eCn, _eS, _eSM],
  [0, 0, 0, 0, 5, 5, () => EndpointConfig$, 0, 0]
];
var MarketplaceModelEndpointSummary$ = [
  3,
  n0,
  _MMES,
  0,
  [_eA, _mSI, _s, _sM, _cA, _uA],
  [0, 0, 0, 0, 5, 5]
];
var MetadataAttributeSchema$ = [
  3,
  n0,
  _MAS,
  8,
  [_k, _ty, _d],
  [0, 0, 0]
];
var MetadataConfigurationForReranking$ = [
  3,
  n0,
  _MCFR,
  0,
  [_sMe, _sMC],
  [0, [() => RerankingMetadataSelectiveModeConfiguration$, 0]]
];
var ModelCopyJobSummary$ = [
  3,
  n0,
  _MCJS,
  0,
  [_jA, _s, _cTr, _tMA, _tMN, _sAI, _sMA, _tMKKA, _tMT, _fMa, _sMN],
  [0, 0, 5, 0, 0, 0, 0, 0, () => TagList, 0, 0]
];
var ModelCustomizationJobSummary$ = [
  3,
  n0,
  _MCJSo,
  0,
  [_jA, _bMA, _jN, _s, _sD, _lMT, _cTr, _eT, _cMA, _cMN, _cTu],
  [0, 0, 0, 0, () => StatusDetails$, 5, 5, 5, 0, 0, 0]
];
var ModelImportJobSummary$ = [
  3,
  n0,
  _MIJS,
  0,
  [_jA, _jN, _s, _lMT, _cTr, _eT, _iMA, _iMN],
  [0, 0, 0, 5, 5, 5, 0, 0]
];
var ModelInvocationJobS3InputDataConfig$ = [
  3,
  n0,
  _MIJSIDC,
  0,
  [_sIF, _sU, _sBO],
  [0, 0, 0]
];
var ModelInvocationJobS3OutputDataConfig$ = [
  3,
  n0,
  _MIJSODC,
  0,
  [_sU, _sEKI, _sBO],
  [0, 0, 0]
];
var ModelInvocationJobSummary$ = [
  3,
  n0,
  _MIJSo,
  0,
  [_jA, _jN, _mIo, _cRT, _rA, _s, _m, _sTu, _lMT, _eT, _iDC, _oDC, _vCp, _tDIH, _jET],
  [0, 0, 0, 0, 0, 0, [() => Message, 0], 5, 5, 5, () => ModelInvocationJobInputDataConfig$, () => ModelInvocationJobOutputDataConfig$, () => VpcConfig$, 1, 5]
];
var Offer$ = [
  3,
  n0,
  _O,
  0,
  [_oI, _oT, _tD],
  [0, 0, () => TermDetails$]
];
var OrchestrationConfiguration$ = [
  3,
  n0,
  _OC,
  0,
  [_qTC],
  [() => QueryTransformationConfiguration$]
];
var OutputDataConfig$ = [
  3,
  n0,
  _ODC,
  0,
  [_sU],
  [0]
];
var PerformanceConfiguration$ = [
  3,
  n0,
  _PC,
  0,
  [_la],
  [0]
];
var PricingTerm$ = [
  3,
  n0,
  _PT,
  0,
  [_rCa],
  [() => RateCard]
];
var PromptRouterSummary$ = [
  3,
  n0,
  _PRS,
  0,
  [_pRN, _rCo, _d, _cA, _uA, _pRA, _mo, _fM, _s, _ty],
  [0, () => RoutingCriteria$, [() => PromptRouterDescription, 0], 5, 5, 0, () => PromptRouterTargetModels, () => PromptRouterTargetModel$, 0, 0]
];
var PromptRouterTargetModel$ = [
  3,
  n0,
  _PRTM,
  0,
  [_mA],
  [0]
];
var PromptTemplate$ = [
  3,
  n0,
  _PTr,
  0,
  [_tPT],
  [[() => TextPromptTemplate, 0]]
];
var ProvisionedModelSummary$ = [
  3,
  n0,
  _PMS,
  0,
  [_pMN, _pMA, _mA, _dMA, _fMA, _mU, _dMU, _s, _cD, _cET, _cTr, _lMT],
  [0, 0, 0, 0, 0, 1, 1, 0, 0, 5, 5, 5]
];
var PutEnforcedGuardrailConfigurationRequest$ = [
  3,
  n0,
  _PEGCR,
  0,
  [_cI, _gIC],
  [0, () => AccountEnforcedGuardrailInferenceInputConfiguration$]
];
var PutEnforcedGuardrailConfigurationResponse$ = [
  3,
  n0,
  _PEGCRu,
  0,
  [_cI, _uA, _uB],
  [0, 5, 0]
];
var PutModelInvocationLoggingConfigurationRequest$ = [
  3,
  n0,
  _PMILCR,
  0,
  [_lC],
  [() => LoggingConfig$]
];
var PutModelInvocationLoggingConfigurationResponse$ = [
  3,
  n0,
  _PMILCRu,
  0,
  [],
  []
];
var PutUseCaseForModelAccessRequest$ = [
  3,
  n0,
  _PUCFMAR,
  0,
  [_fD],
  [21]
];
var PutUseCaseForModelAccessResponse$ = [
  3,
  n0,
  _PUCFMARu,
  0,
  [],
  []
];
var QueryTransformationConfiguration$ = [
  3,
  n0,
  _QTC,
  0,
  [_ty],
  [0]
];
var RatingScaleItem$ = [
  3,
  n0,
  _RSI,
  0,
  [_de, _va],
  [0, () => RatingScaleItemValue$]
];
var RegisterMarketplaceModelEndpointRequest$ = [
  3,
  n0,
  _RMMER,
  0,
  [_eI, _mSI],
  [[0, 1], 0]
];
var RegisterMarketplaceModelEndpointResponse$ = [
  3,
  n0,
  _RMMERe,
  0,
  [_mME],
  [() => MarketplaceModelEndpoint$]
];
var RequestMetadataBaseFilters$ = [
  3,
  n0,
  _RMBF,
  0,
  [_eq, _nE],
  [[() => RequestMetadataMap, 0], [() => RequestMetadataMap, 0]]
];
var ResourceInUseException$ = [
  -3,
  n0,
  _RIUE,
  { [_e]: _c, [_hE]: 400 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ResourceInUseException$, ResourceInUseException);
var ResourceNotFoundException$ = [
  -3,
  n0,
  _RNFE,
  { [_e]: _c, [_hE]: 404 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ResourceNotFoundException$, ResourceNotFoundException);
var RetrieveAndGenerateConfiguration$ = [
  3,
  n0,
  _RAGC,
  0,
  [_ty, _kBC, _eSC],
  [0, [() => KnowledgeBaseRetrieveAndGenerateConfiguration$, 0], [() => ExternalSourcesRetrieveAndGenerateConfiguration$, 0]]
];
var RetrieveConfig$ = [
  3,
  n0,
  _RC,
  0,
  [_kBI, _kBRC],
  [0, [() => KnowledgeBaseRetrievalConfiguration$, 0]]
];
var RFTConfig$ = [
  3,
  n0,
  _RFTC,
  0,
  [_gCr, _hP],
  [() => GraderConfig$, () => RFTHyperParameters$]
];
var RFTHyperParameters$ = [
  3,
  n0,
  _RFTHP,
  0,
  [_eCp, _bSa, _lR, _mPL, _tSPP, _iMTn, _rE, _eIv],
  [1, 1, 1, 1, 1, 1, 0, 1]
];
var RoutingCriteria$ = [
  3,
  n0,
  _RCo,
  0,
  [_rQD],
  [1]
];
var S3Config$ = [
  3,
  n0,
  _SC,
  0,
  [_bN, _kP],
  [0, 0]
];
var S3DataSource$ = [
  3,
  n0,
  _SDS,
  0,
  [_sU],
  [0]
];
var S3ObjectDoc$ = [
  3,
  n0,
  _SOD,
  0,
  [_uri],
  [0]
];
var SageMakerEndpoint$ = [
  3,
  n0,
  _SME,
  0,
  [_iIC, _iTn, _eRx, _kEK, _vp],
  [1, 0, 0, 0, () => VpcConfig$]
];
var ServiceQuotaExceededException$ = [
  -3,
  n0,
  _SQEE,
  { [_e]: _c, [_hE]: 400 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ServiceQuotaExceededException$, ServiceQuotaExceededException);
var ServiceUnavailableException$ = [
  -3,
  n0,
  _SUE,
  { [_e]: _se, [_hE]: 503 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ServiceUnavailableException$, ServiceUnavailableException);
var StartAutomatedReasoningPolicyBuildWorkflowRequest$ = [
  3,
  n0,
  _SARPBWR,
  0,
  [_pA, _bWT, _cRT, _sCo],
  [[0, 1], [0, 1], [0, { [_hH]: _xact, [_iTd]: 1 }], [() => AutomatedReasoningPolicyBuildWorkflowSource$, 16]]
];
var StartAutomatedReasoningPolicyBuildWorkflowResponse$ = [
  3,
  n0,
  _SARPBWRt,
  0,
  [_pA, _bWI],
  [0, 0]
];
var StartAutomatedReasoningPolicyTestWorkflowRequest$ = [
  3,
  n0,
  _SARPTWR,
  0,
  [_pA, _bWI, _tCIe, _cRT],
  [[0, 1], [0, 1], 64 | 0, [0, 4]]
];
var StartAutomatedReasoningPolicyTestWorkflowResponse$ = [
  3,
  n0,
  _SARPTWRt,
  0,
  [_pA],
  [0]
];
var StatusDetails$ = [
  3,
  n0,
  _SD,
  0,
  [_vD, _dPD, _tDr],
  [() => ValidationDetails$, () => DataProcessingDetails$, () => TrainingDetails$]
];
var StopEvaluationJobRequest$ = [
  3,
  n0,
  _SEJR,
  0,
  [_jI],
  [[() => EvaluationJobIdentifier, 1]]
];
var StopEvaluationJobResponse$ = [
  3,
  n0,
  _SEJRt,
  0,
  [],
  []
];
var StopModelCustomizationJobRequest$ = [
  3,
  n0,
  _SMCJR,
  0,
  [_jI],
  [[0, 1]]
];
var StopModelCustomizationJobResponse$ = [
  3,
  n0,
  _SMCJRt,
  0,
  [],
  []
];
var StopModelInvocationJobRequest$ = [
  3,
  n0,
  _SMIJR,
  0,
  [_jI],
  [[0, 1]]
];
var StopModelInvocationJobResponse$ = [
  3,
  n0,
  _SMIJRt,
  0,
  [],
  []
];
var SupportTerm$ = [
  3,
  n0,
  _ST,
  0,
  [_rPD],
  [0]
];
var Tag$ = [
  3,
  n0,
  _T,
  0,
  [_k, _va],
  [0, 0]
];
var TagResourceRequest$ = [
  3,
  n0,
  _TRR,
  0,
  [_rARN, _ta],
  [0, () => TagList]
];
var TagResourceResponse$ = [
  3,
  n0,
  _TRRa,
  0,
  [],
  []
];
var TeacherModelConfig$ = [
  3,
  n0,
  _TMC,
  0,
  [_tMI, _mRLFI],
  [0, 1]
];
var TermDetails$ = [
  3,
  n0,
  _TD,
  0,
  [_uBPT, _lT, _sTup, _vT],
  [() => PricingTerm$, () => LegalTerm$, () => SupportTerm$, () => ValidityTerm$]
];
var TextInferenceConfig$ = [
  3,
  n0,
  _TIC,
  0,
  [_tem, _tPo, _mTa, _sS],
  [1, 1, 1, 64 | 0]
];
var ThrottlingException$ = [
  -3,
  n0,
  _TE,
  { [_e]: _c, [_hE]: 429 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ThrottlingException$, ThrottlingException);
var TooManyTagsException$ = [
  -3,
  n0,
  _TMTE,
  { [_e]: _c, [_hE]: 400 },
  [_m, _rN],
  [0, 0]
];
TypeRegistry.for(n0).registerError(TooManyTagsException$, TooManyTagsException);
var TrainingDataConfig$ = [
  3,
  n0,
  _TDC,
  0,
  [_sU, _iLC],
  [0, [() => InvocationLogsConfig$, 0]]
];
var TrainingDetails$ = [
  3,
  n0,
  _TDr,
  0,
  [_s, _cTr, _lMT],
  [0, 5, 5]
];
var TrainingMetrics$ = [
  3,
  n0,
  _TM,
  0,
  [_tL],
  [1]
];
var UntagResourceRequest$ = [
  3,
  n0,
  _URR,
  0,
  [_rARN, _tK],
  [0, 64 | 0]
];
var UntagResourceResponse$ = [
  3,
  n0,
  _URRn,
  0,
  [],
  []
];
var UpdateAutomatedReasoningPolicyAnnotationsRequest$ = [
  3,
  n0,
  _UARPAR,
  0,
  [_pA, _bWI, _an, _lUASH],
  [[0, 1], [0, 1], [() => AutomatedReasoningPolicyAnnotationList, 0], 0]
];
var UpdateAutomatedReasoningPolicyAnnotationsResponse$ = [
  3,
  n0,
  _UARPARp,
  0,
  [_pA, _bWI, _aSH, _uA],
  [0, 0, 0, 5]
];
var UpdateAutomatedReasoningPolicyRequest$ = [
  3,
  n0,
  _UARPR,
  0,
  [_pA, _pD, _n, _d],
  [[0, 1], [() => AutomatedReasoningPolicyDefinition$, 0], [() => AutomatedReasoningPolicyName, 0], [() => AutomatedReasoningPolicyDescription, 0]]
];
var UpdateAutomatedReasoningPolicyResponse$ = [
  3,
  n0,
  _UARPRp,
  0,
  [_pA, _n, _dH, _uA],
  [0, [() => AutomatedReasoningPolicyName, 0], 0, 5]
];
var UpdateAutomatedReasoningPolicyTestCaseRequest$ = [
  3,
  n0,
  _UARPTCR,
  0,
  [_pA, _tCI, _gC, _qC, _lUA, _eAFR, _cT, _cRT],
  [[0, 1], [0, 1], [() => AutomatedReasoningPolicyTestGuardContent, 0], [() => AutomatedReasoningPolicyTestQueryContent, 0], 5, 0, 1, [0, 4]]
];
var UpdateAutomatedReasoningPolicyTestCaseResponse$ = [
  3,
  n0,
  _UARPTCRp,
  0,
  [_pA, _tCI],
  [0, 0]
];
var UpdateCustomModelDeploymentRequest$ = [
  3,
  n0,
  _UCMDR,
  0,
  [_mA, _cMDI],
  [0, [0, 1]]
];
var UpdateCustomModelDeploymentResponse$ = [
  3,
  n0,
  _UCMDRp,
  0,
  [_cMDA],
  [0]
];
var UpdateGuardrailRequest$ = [
  3,
  n0,
  _UGR,
  0,
  [_gI, _n, _d, _tPC, _cPC, _wPC, _sIPC, _cGPC, _aRPC, _cRC, _bIM, _bOM, _kKI],
  [[0, 1], [() => GuardrailName, 0], [() => GuardrailDescription, 0], [() => GuardrailTopicPolicyConfig$, 0], [() => GuardrailContentPolicyConfig$, 0], [() => GuardrailWordPolicyConfig$, 0], () => GuardrailSensitiveInformationPolicyConfig$, [() => GuardrailContextualGroundingPolicyConfig$, 0], () => GuardrailAutomatedReasoningPolicyConfig$, () => GuardrailCrossRegionConfig$, [() => GuardrailBlockedMessaging, 0], [() => GuardrailBlockedMessaging, 0], 0]
];
var UpdateGuardrailResponse$ = [
  3,
  n0,
  _UGRp,
  0,
  [_gIu, _gA, _ve, _uA],
  [0, 0, 0, 5]
];
var UpdateMarketplaceModelEndpointRequest$ = [
  3,
  n0,
  _UMMER,
  0,
  [_eA, _eCn, _cRT],
  [[0, 1], () => EndpointConfig$, [0, 4]]
];
var UpdateMarketplaceModelEndpointResponse$ = [
  3,
  n0,
  _UMMERp,
  0,
  [_mME],
  [() => MarketplaceModelEndpoint$]
];
var UpdateProvisionedModelThroughputRequest$ = [
  3,
  n0,
  _UPMTR,
  0,
  [_pMI, _dPMN, _dMI],
  [[0, 1], 0, 0]
];
var UpdateProvisionedModelThroughputResponse$ = [
  3,
  n0,
  _UPMTRp,
  0,
  [],
  []
];
var ValidationDataConfig$ = [
  3,
  n0,
  _VDC,
  0,
  [_val],
  [() => Validators]
];
var ValidationDetails$ = [
  3,
  n0,
  _VD,
  0,
  [_s, _cTr, _lMT],
  [0, 5, 5]
];
var ValidationException$ = [
  -3,
  n0,
  _VE,
  { [_e]: _c, [_hE]: 400 },
  [_m],
  [0]
];
TypeRegistry.for(n0).registerError(ValidationException$, ValidationException);
var Validator$ = [
  3,
  n0,
  _V,
  0,
  [_sU],
  [0]
];
var ValidatorMetric$ = [
  3,
  n0,
  _VM,
  0,
  [_vL],
  [1]
];
var ValidityTerm$ = [
  3,
  n0,
  _VT,
  0,
  [_aD],
  [0]
];
var VectorSearchBedrockRerankingConfiguration$ = [
  3,
  n0,
  _VSBRC,
  0,
  [_mC, _nORR, _mCe],
  [() => VectorSearchBedrockRerankingModelConfiguration$, 1, [() => MetadataConfigurationForReranking$, 0]]
];
var VectorSearchBedrockRerankingModelConfiguration$ = [
  3,
  n0,
  _VSBRMC,
  0,
  [_mA, _aMRF],
  [0, 128 | 15]
];
var VectorSearchRerankingConfiguration$ = [
  3,
  n0,
  _VSRC,
  0,
  [_ty, _bRC],
  [0, [() => VectorSearchBedrockRerankingConfiguration$, 0]]
];
var VpcConfig$ = [
  3,
  n0,
  _VC,
  0,
  [_sI, _sGI],
  [64 | 0, 64 | 0]
];
var BedrockServiceException$ = [-3, _sm, "BedrockServiceException", 0, [], []];
TypeRegistry.for(_sm).registerError(BedrockServiceException$, BedrockServiceException);
var AccountEnforcedGuardrailsOutputConfiguration = [
  1,
  n0,
  _AEGOCc,
  0,
  () => AccountEnforcedGuardrailOutputConfiguration$
];
var AutomatedEvaluationCustomMetrics = [
  1,
  n0,
  _AECM,
  0,
  [
    () => AutomatedEvaluationCustomMetricSource$,
    0
  ]
];
var AutomatedReasoningCheckDifferenceScenarioList = [
  1,
  n0,
  _ARCDSL,
  0,
  [
    () => AutomatedReasoningCheckScenario$,
    0
  ]
];
var AutomatedReasoningCheckFindingList = [
  1,
  n0,
  _ARCFL,
  0,
  [
    () => AutomatedReasoningCheckFinding$,
    0
  ]
];
var AutomatedReasoningCheckInputTextReferenceList = [
  1,
  n0,
  _ARCITRL,
  0,
  [
    () => AutomatedReasoningCheckInputTextReference$,
    0
  ]
];
var AutomatedReasoningCheckRuleList = [
  1,
  n0,
  _ARCRL,
  0,
  () => AutomatedReasoningCheckRule$
];
var AutomatedReasoningCheckTranslationList = [
  1,
  n0,
  _ARCTL,
  0,
  [
    () => AutomatedReasoningCheckTranslation$,
    0
  ]
];
var AutomatedReasoningCheckTranslationOptionList = [
  1,
  n0,
  _ARCTOL,
  0,
  [
    () => AutomatedReasoningCheckTranslationOption$,
    0
  ]
];
var AutomatedReasoningLogicStatementList = [
  1,
  n0,
  _ARLSL,
  0,
  [
    () => AutomatedReasoningLogicStatement$,
    0
  ]
];
var AutomatedReasoningPolicyAnnotationList = [
  1,
  n0,
  _ARPAL,
  0,
  [
    () => AutomatedReasoningPolicyAnnotation$,
    0
  ]
];
var AutomatedReasoningPolicyArnList = 64 | 0;
var AutomatedReasoningPolicyBuildLogEntryList = [
  1,
  n0,
  _ARPBLEL,
  0,
  [
    () => AutomatedReasoningPolicyBuildLogEntry$,
    0
  ]
];
var AutomatedReasoningPolicyBuildStepList = [
  1,
  n0,
  _ARPBSL,
  0,
  [
    () => AutomatedReasoningPolicyBuildStep$,
    0
  ]
];
var AutomatedReasoningPolicyBuildStepMessageList = [
  1,
  n0,
  _ARPBSML,
  0,
  () => AutomatedReasoningPolicyBuildStepMessage$
];
var AutomatedReasoningPolicyBuildWorkflowDocumentList = [
  1,
  n0,
  _ARPBWDL,
  0,
  [
    () => AutomatedReasoningPolicyBuildWorkflowDocument$,
    0
  ]
];
var AutomatedReasoningPolicyBuildWorkflowSummaries = [
  1,
  n0,
  _ARPBWSut,
  0,
  () => AutomatedReasoningPolicyBuildWorkflowSummary$
];
var AutomatedReasoningPolicyConflictedRuleIdList = 64 | 0;
var AutomatedReasoningPolicyDefinitionRuleIdList = 64 | 0;
var AutomatedReasoningPolicyDefinitionRuleList = [
  1,
  n0,
  _ARPDRL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionRule$,
    0
  ]
];
var AutomatedReasoningPolicyDefinitionTypeList = [
  1,
  n0,
  _ARPDTL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionType$,
    0
  ]
];
var AutomatedReasoningPolicyDefinitionTypeNameList = [
  1,
  n0,
  _ARPDTNL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionTypeName,
    0
  ]
];
var AutomatedReasoningPolicyDefinitionTypeValueList = [
  1,
  n0,
  _ARPDTVL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionTypeValue$,
    0
  ]
];
var AutomatedReasoningPolicyDefinitionTypeValuePairList = [
  1,
  n0,
  _ARPDTVPL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionTypeValuePair$,
    0
  ]
];
var AutomatedReasoningPolicyDefinitionVariableList = [
  1,
  n0,
  _ARPDVL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionVariable$,
    0
  ]
];
var AutomatedReasoningPolicyDefinitionVariableNameList = [
  1,
  n0,
  _ARPDVNL,
  0,
  [
    () => AutomatedReasoningPolicyDefinitionVariableName,
    0
  ]
];
var AutomatedReasoningPolicyDisjointedRuleIdList = 64 | 0;
var AutomatedReasoningPolicyDisjointRuleSetList = [
  1,
  n0,
  _ARPDRSL,
  0,
  [
    () => AutomatedReasoningPolicyDisjointRuleSet$,
    0
  ]
];
var AutomatedReasoningPolicyGeneratedTestCaseList = [
  1,
  n0,
  _ARPGTCL,
  0,
  [
    () => AutomatedReasoningPolicyGeneratedTestCase$,
    0
  ]
];
var AutomatedReasoningPolicyScenarioList = [
  1,
  n0,
  _ARPSL,
  0,
  [
    () => AutomatedReasoningPolicyScenario$,
    0
  ]
];
var AutomatedReasoningPolicySummaries = [
  1,
  n0,
  _ARPSuto,
  0,
  [
    () => AutomatedReasoningPolicySummary$,
    0
  ]
];
var AutomatedReasoningPolicyTestCaseIdList = 64 | 0;
var AutomatedReasoningPolicyTestCaseList = [
  1,
  n0,
  _ARPTCL,
  0,
  [
    () => AutomatedReasoningPolicyTestCase$,
    0
  ]
];
var AutomatedReasoningPolicyTestList = [
  1,
  n0,
  _ARPTL,
  0,
  [
    () => AutomatedReasoningPolicyTestResult$,
    0
  ]
];
var AutomatedReasoningPolicyTypeValueAnnotationList = [
  1,
  n0,
  _ARPTVAL,
  0,
  [
    () => AutomatedReasoningPolicyTypeValueAnnotation$,
    0
  ]
];
var BatchDeleteEvaluationJobErrors = [
  1,
  n0,
  _BDEJEa,
  0,
  [
    () => BatchDeleteEvaluationJobError$,
    0
  ]
];
var BatchDeleteEvaluationJobItems = [
  1,
  n0,
  _BDEJIa,
  0,
  [
    () => BatchDeleteEvaluationJobItem$,
    0
  ]
];
var BedrockEvaluatorModels = [
  1,
  n0,
  _BEMe,
  0,
  () => BedrockEvaluatorModel$
];
var CustomMetricBedrockEvaluatorModels = [
  1,
  n0,
  _CMBEMu,
  0,
  () => CustomMetricBedrockEvaluatorModel$
];
var CustomModelDeploymentSummaryList = [
  1,
  n0,
  _CMDSL,
  0,
  () => CustomModelDeploymentSummary$
];
var CustomModelSummaryList = [
  1,
  n0,
  _CMSL,
  0,
  () => CustomModelSummary$
];
var ErrorMessages = 64 | 0;
var EvaluationBedrockKnowledgeBaseIdentifiers = 64 | 0;
var EvaluationBedrockModelIdentifiers = 64 | 0;
var EvaluationDatasetMetricConfigs = [
  1,
  n0,
  _EDMCv,
  0,
  [
    () => EvaluationDatasetMetricConfig$,
    0
  ]
];
var EvaluationJobIdentifiers = [
  1,
  n0,
  _EJIv,
  0,
  [
    () => EvaluationJobIdentifier,
    0
  ]
];
var EvaluationMetricNames = [
  1,
  n0,
  _EMNv,
  0,
  [
    () => EvaluationMetricName,
    0
  ]
];
var EvaluationModelConfigs = [
  1,
  n0,
  _EMC,
  0,
  [
    () => EvaluationModelConfig$,
    0
  ]
];
var EvaluationPrecomputedInferenceSourceIdentifiers = 64 | 0;
var EvaluationPrecomputedRagSourceIdentifiers = 64 | 0;
var EvaluationSummaries = [
  1,
  n0,
  _ESv,
  0,
  () => EvaluationSummary$
];
var EvaluationTaskTypes = 64 | 0;
var EvaluatorModelIdentifiers = 64 | 0;
var ExternalSources = [
  1,
  n0,
  _ESxt,
  0,
  [
    () => ExternalSource$,
    0
  ]
];
var FieldsForReranking = [
  1,
  n0,
  _FFRi,
  8,
  () => FieldForReranking$
];
var FoundationModelSummaryList = [
  1,
  n0,
  _FMSL,
  0,
  () => FoundationModelSummary$
];
var GuardrailContentFilters = [
  1,
  n0,
  _GCFu,
  0,
  [
    () => GuardrailContentFilter$,
    0
  ]
];
var GuardrailContentFiltersConfig = [
  1,
  n0,
  _GCFCu,
  0,
  [
    () => GuardrailContentFilterConfig$,
    0
  ]
];
var GuardrailContextualGroundingFilters = [
  1,
  n0,
  _GCGFu,
  0,
  [
    () => GuardrailContextualGroundingFilter$,
    0
  ]
];
var GuardrailContextualGroundingFiltersConfig = [
  1,
  n0,
  _GCGFCu,
  0,
  [
    () => GuardrailContextualGroundingFilterConfig$,
    0
  ]
];
var GuardrailFailureRecommendations = [
  1,
  n0,
  _GFRu,
  0,
  [
    () => GuardrailFailureRecommendation,
    0
  ]
];
var GuardrailManagedWordLists = [
  1,
  n0,
  _GMWL,
  0,
  [
    () => GuardrailManagedWords$,
    0
  ]
];
var GuardrailManagedWordListsConfig = [
  1,
  n0,
  _GMWLC,
  0,
  [
    () => GuardrailManagedWordsConfig$,
    0
  ]
];
var GuardrailModalities = [
  1,
  n0,
  _GMu,
  0,
  [
    () => GuardrailModality,
    0
  ]
];
var GuardrailPiiEntities = [
  1,
  n0,
  _GPEu,
  0,
  () => GuardrailPiiEntity$
];
var GuardrailPiiEntitiesConfig = [
  1,
  n0,
  _GPECu,
  0,
  () => GuardrailPiiEntityConfig$
];
var GuardrailRegexes = [
  1,
  n0,
  _GRu,
  0,
  () => GuardrailRegex$
];
var GuardrailRegexesConfig = [
  1,
  n0,
  _GRCu,
  0,
  () => GuardrailRegexConfig$
];
var GuardrailStatusReasons = [
  1,
  n0,
  _GSRu,
  0,
  [
    () => GuardrailStatusReason,
    0
  ]
];
var GuardrailSummaries = [
  1,
  n0,
  _GSu,
  0,
  [
    () => GuardrailSummary$,
    0
  ]
];
var GuardrailTopicExamples = [
  1,
  n0,
  _GTEu,
  0,
  [
    () => GuardrailTopicExample,
    0
  ]
];
var GuardrailTopics = [
  1,
  n0,
  _GTu,
  0,
  [
    () => GuardrailTopic$,
    0
  ]
];
var GuardrailTopicsConfig = [
  1,
  n0,
  _GTCu,
  0,
  [
    () => GuardrailTopicConfig$,
    0
  ]
];
var GuardrailWords = [
  1,
  n0,
  _GWu,
  0,
  [
    () => GuardrailWord$,
    0
  ]
];
var GuardrailWordsConfig = [
  1,
  n0,
  _GWCu,
  0,
  [
    () => GuardrailWordConfig$,
    0
  ]
];
var HumanEvaluationCustomMetrics = [
  1,
  n0,
  _HECMu,
  0,
  [
    () => HumanEvaluationCustomMetric$,
    0
  ]
];
var ImportedModelSummaryList = [
  1,
  n0,
  _IMSL,
  0,
  () => ImportedModelSummary$
];
var InferenceProfileModels = [
  1,
  n0,
  _IPMn,
  0,
  () => InferenceProfileModel$
];
var InferenceProfileSummaries = [
  1,
  n0,
  _IPSn,
  0,
  [
    () => InferenceProfileSummary$,
    0
  ]
];
var InferenceTypeList = 64 | 0;
var MarketplaceModelEndpointSummaries = [
  1,
  n0,
  _MMESa,
  0,
  () => MarketplaceModelEndpointSummary$
];
var MetadataAttributeSchemaList = [
  1,
  n0,
  _MASL,
  0,
  [
    () => MetadataAttributeSchema$,
    0
  ]
];
var ModelCopyJobSummaries = [
  1,
  n0,
  _MCJSod,
  0,
  () => ModelCopyJobSummary$
];
var ModelCustomizationJobSummaries = [
  1,
  n0,
  _MCJSode,
  0,
  () => ModelCustomizationJobSummary$
];
var ModelCustomizationList = 64 | 0;
var ModelImportJobSummaries = [
  1,
  n0,
  _MIJSod,
  0,
  () => ModelImportJobSummary$
];
var ModelInvocationJobSummaries = [
  1,
  n0,
  _MIJSode,
  0,
  [
    () => ModelInvocationJobSummary$,
    0
  ]
];
var ModelModalityList = 64 | 0;
var Offers = [
  1,
  n0,
  _Of,
  0,
  () => Offer$
];
var PromptRouterSummaries = [
  1,
  n0,
  _PRSr,
  0,
  [
    () => PromptRouterSummary$,
    0
  ]
];
var PromptRouterTargetModels = [
  1,
  n0,
  _PRTMr,
  0,
  () => PromptRouterTargetModel$
];
var ProvisionedModelSummaries = [
  1,
  n0,
  _PMSr,
  0,
  () => ProvisionedModelSummary$
];
var RagConfigs = [
  1,
  n0,
  _RCa,
  0,
  [
    () => RAGConfig$,
    0
  ]
];
var RAGStopSequences = 64 | 0;
var RateCard = [
  1,
  n0,
  _RCat,
  0,
  () => DimensionalPriceRate$
];
var RatingScale = [
  1,
  n0,
  _RS,
  0,
  () => RatingScaleItem$
];
var RequestMetadataFiltersList = [
  1,
  n0,
  _RMFL,
  0,
  [
    () => RequestMetadataBaseFilters$,
    0
  ]
];
var RetrievalFilterList = [
  1,
  n0,
  _RFL,
  0,
  [
    () => RetrievalFilter$,
    0
  ]
];
var SecurityGroupIds = 64 | 0;
var SubnetIds = 64 | 0;
var TagKeyList = 64 | 0;
var TagList = [
  1,
  n0,
  _TL,
  0,
  () => Tag$
];
var ValidationMetrics = [
  1,
  n0,
  _VMa,
  0,
  () => ValidatorMetric$
];
var Validators = [
  1,
  n0,
  _Va,
  0,
  () => Validator$
];
var AdditionalModelRequestFields = 128 | 15;
var ModelCustomizationHyperParameters = 128 | 0;
var RequestMetadataMap = [
  2,
  n0,
  _RMM,
  8,
  0,
  0
];
var AutomatedEvaluationCustomMetricSource$ = [
  4,
  n0,
  _AECMS,
  0,
  [_cMD],
  [[() => CustomMetricDefinition$, 0]]
];
var AutomatedReasoningCheckFinding$ = [
  4,
  n0,
  _ARCF,
  0,
  [_vali, _inv, _sa, _im, _tA, _tCoo, _nTo],
  [[() => AutomatedReasoningCheckValidFinding$, 0], [() => AutomatedReasoningCheckInvalidFinding$, 0], [() => AutomatedReasoningCheckSatisfiableFinding$, 0], [() => AutomatedReasoningCheckImpossibleFinding$, 0], [() => AutomatedReasoningCheckTranslationAmbiguousFinding$, 0], () => AutomatedReasoningCheckTooComplexFinding$, () => AutomatedReasoningCheckNoTranslationsFinding$]
];
var AutomatedReasoningPolicyAnnotation$ = [
  4,
  n0,
  _ARPA,
  0,
  [_aTd, _uTp, _dT, _aV, _uVp, _dV, _aR, _uR, _dR, _aRFNL, _uFRF, _uFSF, _iCn],
  [[() => AutomatedReasoningPolicyAddTypeAnnotation$, 0], [() => AutomatedReasoningPolicyUpdateTypeAnnotation$, 0], [() => AutomatedReasoningPolicyDeleteTypeAnnotation$, 0], [() => AutomatedReasoningPolicyAddVariableAnnotation$, 0], [() => AutomatedReasoningPolicyUpdateVariableAnnotation$, 0], [() => AutomatedReasoningPolicyDeleteVariableAnnotation$, 0], [() => AutomatedReasoningPolicyAddRuleAnnotation$, 0], [() => AutomatedReasoningPolicyUpdateRuleAnnotation$, 0], () => AutomatedReasoningPolicyDeleteRuleAnnotation$, [() => AutomatedReasoningPolicyAddRuleFromNaturalLanguageAnnotation$, 0], [() => AutomatedReasoningPolicyUpdateFromRuleFeedbackAnnotation$, 0], [() => AutomatedReasoningPolicyUpdateFromScenarioFeedbackAnnotation$, 0], [() => AutomatedReasoningPolicyIngestContentAnnotation$, 0]]
];
var AutomatedReasoningPolicyBuildResultAssets$ = [
  4,
  n0,
  _ARPBRA,
  0,
  [_pD, _qR, _bL, _gTC, _pS],
  [[() => AutomatedReasoningPolicyDefinition$, 0], [() => AutomatedReasoningPolicyDefinitionQualityReport$, 0], [() => AutomatedReasoningPolicyBuildLog$, 0], [() => AutomatedReasoningPolicyGeneratedTestCases$, 0], [() => AutomatedReasoningPolicyScenarios$, 0]]
];
var AutomatedReasoningPolicyBuildStepContext$ = [
  4,
  n0,
  _ARPBSC,
  0,
  [_pl, _mu],
  [() => AutomatedReasoningPolicyPlanning$, [() => AutomatedReasoningPolicyMutation$, 0]]
];
var AutomatedReasoningPolicyDefinitionElement$ = [
  4,
  n0,
  _ARPDE,
  0,
  [_pDV, _pDT, _pDR],
  [[() => AutomatedReasoningPolicyDefinitionVariable$, 0], [() => AutomatedReasoningPolicyDefinitionType$, 0], [() => AutomatedReasoningPolicyDefinitionRule$, 0]]
];
var AutomatedReasoningPolicyMutation$ = [
  4,
  n0,
  _ARPM,
  0,
  [_aTd, _uTp, _dT, _aV, _uVp, _dV, _aR, _uR, _dR],
  [[() => AutomatedReasoningPolicyAddTypeMutation$, 0], [() => AutomatedReasoningPolicyUpdateTypeMutation$, 0], [() => AutomatedReasoningPolicyDeleteTypeMutation$, 0], [() => AutomatedReasoningPolicyAddVariableMutation$, 0], [() => AutomatedReasoningPolicyUpdateVariableMutation$, 0], [() => AutomatedReasoningPolicyDeleteVariableMutation$, 0], [() => AutomatedReasoningPolicyAddRuleMutation$, 0], [() => AutomatedReasoningPolicyUpdateRuleMutation$, 0], () => AutomatedReasoningPolicyDeleteRuleMutation$]
];
var AutomatedReasoningPolicyTypeValueAnnotation$ = [
  4,
  n0,
  _ARPTVA,
  0,
  [_aTV, _uTVp, _dTV],
  [[() => AutomatedReasoningPolicyAddTypeValue$, 0], [() => AutomatedReasoningPolicyUpdateTypeValue$, 0], () => AutomatedReasoningPolicyDeleteTypeValue$]
];
var AutomatedReasoningPolicyWorkflowTypeContent$ = [
  4,
  n0,
  _ARPWTC,
  0,
  [_doc, _pRAo],
  [[() => AutomatedReasoningPolicyBuildWorkflowDocumentList, 0], [() => AutomatedReasoningPolicyBuildWorkflowRepairContent$, 0]]
];
var CustomizationConfig$ = [
  4,
  n0,
  _CC,
  0,
  [_dC, _rCf],
  [() => DistillationConfig$, () => RFTConfig$]
];
var EndpointConfig$ = [
  4,
  n0,
  _EC,
  0,
  [_sMa],
  [() => SageMakerEndpoint$]
];
var EvaluationConfig$ = [
  4,
  n0,
  _ECv,
  0,
  [_au, _h],
  [[() => AutomatedEvaluationConfig$, 0], [() => HumanEvaluationConfig$, 0]]
];
var EvaluationDatasetLocation$ = [
  4,
  n0,
  _EDL,
  0,
  [_sU],
  [0]
];
var EvaluationInferenceConfig$ = [
  4,
  n0,
  _EIC,
  0,
  [_mo, _rCag],
  [[() => EvaluationModelConfigs, 0], [() => RagConfigs, 0]]
];
var EvaluationModelConfig$ = [
  4,
  n0,
  _EMCv,
  0,
  [_bM, _pIS],
  [[() => EvaluationBedrockModel$, 0], () => EvaluationPrecomputedInferenceSource$]
];
var EvaluationPrecomputedRagSourceConfig$ = [
  4,
  n0,
  _EPRSCv,
  0,
  [_rSC, _rAGSC],
  [() => EvaluationPrecomputedRetrieveSourceConfig$, () => EvaluationPrecomputedRetrieveAndGenerateSourceConfig$]
];
var EvaluatorModelConfig$ = [
  4,
  n0,
  _EMCva,
  0,
  [_bEM],
  [() => BedrockEvaluatorModels]
];
var GraderConfig$ = [
  4,
  n0,
  _GCr,
  0,
  [_lG],
  [() => LambdaGraderConfig$]
];
var InferenceProfileModelSource$ = [
  4,
  n0,
  _IPMS,
  0,
  [_cF],
  [0]
];
var InvocationLogSource$ = [
  4,
  n0,
  _ILS,
  0,
  [_sU],
  [0]
];
var KnowledgeBaseConfig$ = [
  4,
  n0,
  _KBC,
  0,
  [_rCetr, _rAGC],
  [[() => RetrieveConfig$, 0], [() => RetrieveAndGenerateConfiguration$, 0]]
];
var ModelDataSource$ = [
  4,
  n0,
  _MDS,
  0,
  [_sDS],
  [() => S3DataSource$]
];
var ModelInvocationJobInputDataConfig$ = [
  4,
  n0,
  _MIJIDC,
  0,
  [_sIDC],
  [() => ModelInvocationJobS3InputDataConfig$]
];
var ModelInvocationJobOutputDataConfig$ = [
  4,
  n0,
  _MIJODC,
  0,
  [_sODC],
  [() => ModelInvocationJobS3OutputDataConfig$]
];
var RAGConfig$ = [
  4,
  n0,
  _RAGCo,
  0,
  [_kBCn, _pRSC],
  [[() => KnowledgeBaseConfig$, 0], () => EvaluationPrecomputedRagSourceConfig$]
];
var RatingScaleItemValue$ = [
  4,
  n0,
  _RSIV,
  0,
  [_sV, _fV],
  [0, 1]
];
var RequestMetadataFilters$ = [
  4,
  n0,
  _RMF,
  0,
  [_eq, _nE, _aAn, _oAr],
  [[() => RequestMetadataMap, 0], [() => RequestMetadataMap, 0], [() => RequestMetadataFiltersList, 0], [() => RequestMetadataFiltersList, 0]]
];
var RerankingMetadataSelectiveModeConfiguration$ = [
  4,
  n0,
  _RMSMC,
  0,
  [_fTI, _fTE],
  [[() => FieldsForReranking, 0], [() => FieldsForReranking, 0]]
];
var RetrievalFilter$ = [
  4,
  n0,
  _RF,
  8,
  [_eq, _nE, _gT, _gTOE, _lTe, _lTOE, _in_, _nI, _sW, _lCi, _sCt, _aAn, _oAr],
  [() => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, () => FilterAttribute$, [() => RetrievalFilterList, 0], [() => RetrievalFilterList, 0]]
];
var BatchDeleteEvaluationJob$ = [
  9,
  n0,
  _BDEJ,
  { [_ht]: ["POST", "/evaluation-jobs/batch-delete", 202] },
  () => BatchDeleteEvaluationJobRequest$,
  () => BatchDeleteEvaluationJobResponse$
];
var CancelAutomatedReasoningPolicyBuildWorkflow$ = [
  9,
  n0,
  _CARPBW,
  { [_ht]: ["POST", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/cancel", 202] },
  () => CancelAutomatedReasoningPolicyBuildWorkflowRequest$,
  () => CancelAutomatedReasoningPolicyBuildWorkflowResponse$
];
var CreateAutomatedReasoningPolicy$ = [
  9,
  n0,
  _CARP,
  { [_ht]: ["POST", "/automated-reasoning-policies", 200] },
  () => CreateAutomatedReasoningPolicyRequest$,
  () => CreateAutomatedReasoningPolicyResponse$
];
var CreateAutomatedReasoningPolicyTestCase$ = [
  9,
  n0,
  _CARPTC,
  { [_ht]: ["POST", "/automated-reasoning-policies/{policyArn}/test-cases", 200] },
  () => CreateAutomatedReasoningPolicyTestCaseRequest$,
  () => CreateAutomatedReasoningPolicyTestCaseResponse$
];
var CreateAutomatedReasoningPolicyVersion$ = [
  9,
  n0,
  _CARPV,
  { [_ht]: ["POST", "/automated-reasoning-policies/{policyArn}/versions", 200] },
  () => CreateAutomatedReasoningPolicyVersionRequest$,
  () => CreateAutomatedReasoningPolicyVersionResponse$
];
var CreateCustomModel$ = [
  9,
  n0,
  _CCM,
  { [_ht]: ["POST", "/custom-models/create-custom-model", 202] },
  () => CreateCustomModelRequest$,
  () => CreateCustomModelResponse$
];
var CreateCustomModelDeployment$ = [
  9,
  n0,
  _CCMD,
  { [_ht]: ["POST", "/model-customization/custom-model-deployments", 202] },
  () => CreateCustomModelDeploymentRequest$,
  () => CreateCustomModelDeploymentResponse$
];
var CreateEvaluationJob$ = [
  9,
  n0,
  _CEJ,
  { [_ht]: ["POST", "/evaluation-jobs", 202] },
  () => CreateEvaluationJobRequest$,
  () => CreateEvaluationJobResponse$
];
var CreateFoundationModelAgreement$ = [
  9,
  n0,
  _CFMA,
  { [_ht]: ["POST", "/create-foundation-model-agreement", 202] },
  () => CreateFoundationModelAgreementRequest$,
  () => CreateFoundationModelAgreementResponse$
];
var CreateGuardrail$ = [
  9,
  n0,
  _CG,
  { [_ht]: ["POST", "/guardrails", 202] },
  () => CreateGuardrailRequest$,
  () => CreateGuardrailResponse$
];
var CreateGuardrailVersion$ = [
  9,
  n0,
  _CGV,
  { [_ht]: ["POST", "/guardrails/{guardrailIdentifier}", 202] },
  () => CreateGuardrailVersionRequest$,
  () => CreateGuardrailVersionResponse$
];
var CreateInferenceProfile$ = [
  9,
  n0,
  _CIP,
  { [_ht]: ["POST", "/inference-profiles", 201] },
  () => CreateInferenceProfileRequest$,
  () => CreateInferenceProfileResponse$
];
var CreateMarketplaceModelEndpoint$ = [
  9,
  n0,
  _CMME,
  { [_ht]: ["POST", "/marketplace-model/endpoints", 200] },
  () => CreateMarketplaceModelEndpointRequest$,
  () => CreateMarketplaceModelEndpointResponse$
];
var CreateModelCopyJob$ = [
  9,
  n0,
  _CMCJ,
  { [_ht]: ["POST", "/model-copy-jobs", 201] },
  () => CreateModelCopyJobRequest$,
  () => CreateModelCopyJobResponse$
];
var CreateModelCustomizationJob$ = [
  9,
  n0,
  _CMCJr,
  { [_ht]: ["POST", "/model-customization-jobs", 201] },
  () => CreateModelCustomizationJobRequest$,
  () => CreateModelCustomizationJobResponse$
];
var CreateModelImportJob$ = [
  9,
  n0,
  _CMIJ,
  { [_ht]: ["POST", "/model-import-jobs", 201] },
  () => CreateModelImportJobRequest$,
  () => CreateModelImportJobResponse$
];
var CreateModelInvocationJob$ = [
  9,
  n0,
  _CMIJr,
  { [_ht]: ["POST", "/model-invocation-job", 200] },
  () => CreateModelInvocationJobRequest$,
  () => CreateModelInvocationJobResponse$
];
var CreatePromptRouter$ = [
  9,
  n0,
  _CPR,
  { [_ht]: ["POST", "/prompt-routers", 200] },
  () => CreatePromptRouterRequest$,
  () => CreatePromptRouterResponse$
];
var CreateProvisionedModelThroughput$ = [
  9,
  n0,
  _CPMT,
  { [_ht]: ["POST", "/provisioned-model-throughput", 201] },
  () => CreateProvisionedModelThroughputRequest$,
  () => CreateProvisionedModelThroughputResponse$
];
var DeleteAutomatedReasoningPolicy$ = [
  9,
  n0,
  _DARP,
  { [_ht]: ["DELETE", "/automated-reasoning-policies/{policyArn}", 202] },
  () => DeleteAutomatedReasoningPolicyRequest$,
  () => DeleteAutomatedReasoningPolicyResponse$
];
var DeleteAutomatedReasoningPolicyBuildWorkflow$ = [
  9,
  n0,
  _DARPBW,
  { [_ht]: ["DELETE", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}", 202] },
  () => DeleteAutomatedReasoningPolicyBuildWorkflowRequest$,
  () => DeleteAutomatedReasoningPolicyBuildWorkflowResponse$
];
var DeleteAutomatedReasoningPolicyTestCase$ = [
  9,
  n0,
  _DARPTC,
  { [_ht]: ["DELETE", "/automated-reasoning-policies/{policyArn}/test-cases/{testCaseId}", 202] },
  () => DeleteAutomatedReasoningPolicyTestCaseRequest$,
  () => DeleteAutomatedReasoningPolicyTestCaseResponse$
];
var DeleteCustomModel$ = [
  9,
  n0,
  _DCM,
  { [_ht]: ["DELETE", "/custom-models/{modelIdentifier}", 200] },
  () => DeleteCustomModelRequest$,
  () => DeleteCustomModelResponse$
];
var DeleteCustomModelDeployment$ = [
  9,
  n0,
  _DCMD,
  { [_ht]: ["DELETE", "/model-customization/custom-model-deployments/{customModelDeploymentIdentifier}", 200] },
  () => DeleteCustomModelDeploymentRequest$,
  () => DeleteCustomModelDeploymentResponse$
];
var DeleteEnforcedGuardrailConfiguration$ = [
  9,
  n0,
  _DEGC,
  { [_ht]: ["DELETE", "/enforcedGuardrailsConfiguration/{configId}", 200] },
  () => DeleteEnforcedGuardrailConfigurationRequest$,
  () => DeleteEnforcedGuardrailConfigurationResponse$
];
var DeleteFoundationModelAgreement$ = [
  9,
  n0,
  _DFMA,
  { [_ht]: ["POST", "/delete-foundation-model-agreement", 202] },
  () => DeleteFoundationModelAgreementRequest$,
  () => DeleteFoundationModelAgreementResponse$
];
var DeleteGuardrail$ = [
  9,
  n0,
  _DG,
  { [_ht]: ["DELETE", "/guardrails/{guardrailIdentifier}", 202] },
  () => DeleteGuardrailRequest$,
  () => DeleteGuardrailResponse$
];
var DeleteImportedModel$ = [
  9,
  n0,
  _DIM,
  { [_ht]: ["DELETE", "/imported-models/{modelIdentifier}", 200] },
  () => DeleteImportedModelRequest$,
  () => DeleteImportedModelResponse$
];
var DeleteInferenceProfile$ = [
  9,
  n0,
  _DIP,
  { [_ht]: ["DELETE", "/inference-profiles/{inferenceProfileIdentifier}", 200] },
  () => DeleteInferenceProfileRequest$,
  () => DeleteInferenceProfileResponse$
];
var DeleteMarketplaceModelEndpoint$ = [
  9,
  n0,
  _DMME,
  { [_ht]: ["DELETE", "/marketplace-model/endpoints/{endpointArn}", 200] },
  () => DeleteMarketplaceModelEndpointRequest$,
  () => DeleteMarketplaceModelEndpointResponse$
];
var DeleteModelInvocationLoggingConfiguration$ = [
  9,
  n0,
  _DMILC,
  { [_ht]: ["DELETE", "/logging/modelinvocations", 200] },
  () => DeleteModelInvocationLoggingConfigurationRequest$,
  () => DeleteModelInvocationLoggingConfigurationResponse$
];
var DeletePromptRouter$ = [
  9,
  n0,
  _DPRe,
  { [_ht]: ["DELETE", "/prompt-routers/{promptRouterArn}", 200] },
  () => DeletePromptRouterRequest$,
  () => DeletePromptRouterResponse$
];
var DeleteProvisionedModelThroughput$ = [
  9,
  n0,
  _DPMT,
  { [_ht]: ["DELETE", "/provisioned-model-throughput/{provisionedModelId}", 200] },
  () => DeleteProvisionedModelThroughputRequest$,
  () => DeleteProvisionedModelThroughputResponse$
];
var DeregisterMarketplaceModelEndpoint$ = [
  9,
  n0,
  _DMMEe,
  { [_ht]: ["DELETE", "/marketplace-model/endpoints/{endpointArn}/registration", 200] },
  () => DeregisterMarketplaceModelEndpointRequest$,
  () => DeregisterMarketplaceModelEndpointResponse$
];
var ExportAutomatedReasoningPolicyVersion$ = [
  9,
  n0,
  _EARPV,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/export", 200] },
  () => ExportAutomatedReasoningPolicyVersionRequest$,
  () => ExportAutomatedReasoningPolicyVersionResponse$
];
var GetAutomatedReasoningPolicy$ = [
  9,
  n0,
  _GARPe,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}", 200] },
  () => GetAutomatedReasoningPolicyRequest$,
  () => GetAutomatedReasoningPolicyResponse$
];
var GetAutomatedReasoningPolicyAnnotations$ = [
  9,
  n0,
  _GARPA,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/annotations", 200] },
  () => GetAutomatedReasoningPolicyAnnotationsRequest$,
  () => GetAutomatedReasoningPolicyAnnotationsResponse$
];
var GetAutomatedReasoningPolicyBuildWorkflow$ = [
  9,
  n0,
  _GARPBW,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}", 200] },
  () => GetAutomatedReasoningPolicyBuildWorkflowRequest$,
  () => GetAutomatedReasoningPolicyBuildWorkflowResponse$
];
var GetAutomatedReasoningPolicyBuildWorkflowResultAssets$ = [
  9,
  n0,
  _GARPBWRA,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/result-assets", 200] },
  () => GetAutomatedReasoningPolicyBuildWorkflowResultAssetsRequest$,
  () => GetAutomatedReasoningPolicyBuildWorkflowResultAssetsResponse$
];
var GetAutomatedReasoningPolicyNextScenario$ = [
  9,
  n0,
  _GARPNS,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/scenarios", 200] },
  () => GetAutomatedReasoningPolicyNextScenarioRequest$,
  () => GetAutomatedReasoningPolicyNextScenarioResponse$
];
var GetAutomatedReasoningPolicyTestCase$ = [
  9,
  n0,
  _GARPTC,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/test-cases/{testCaseId}", 200] },
  () => GetAutomatedReasoningPolicyTestCaseRequest$,
  () => GetAutomatedReasoningPolicyTestCaseResponse$
];
var GetAutomatedReasoningPolicyTestResult$ = [
  9,
  n0,
  _GARPTR,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/test-cases/{testCaseId}/test-results", 200] },
  () => GetAutomatedReasoningPolicyTestResultRequest$,
  () => GetAutomatedReasoningPolicyTestResultResponse$
];
var GetCustomModel$ = [
  9,
  n0,
  _GCM,
  { [_ht]: ["GET", "/custom-models/{modelIdentifier}", 200] },
  () => GetCustomModelRequest$,
  () => GetCustomModelResponse$
];
var GetCustomModelDeployment$ = [
  9,
  n0,
  _GCMD,
  { [_ht]: ["GET", "/model-customization/custom-model-deployments/{customModelDeploymentIdentifier}", 200] },
  () => GetCustomModelDeploymentRequest$,
  () => GetCustomModelDeploymentResponse$
];
var GetEvaluationJob$ = [
  9,
  n0,
  _GEJ,
  { [_ht]: ["GET", "/evaluation-jobs/{jobIdentifier}", 200] },
  () => GetEvaluationJobRequest$,
  () => GetEvaluationJobResponse$
];
var GetFoundationModel$ = [
  9,
  n0,
  _GFM,
  { [_ht]: ["GET", "/foundation-models/{modelIdentifier}", 200] },
  () => GetFoundationModelRequest$,
  () => GetFoundationModelResponse$
];
var GetFoundationModelAvailability$ = [
  9,
  n0,
  _GFMA,
  { [_ht]: ["GET", "/foundation-model-availability/{modelId}", 200] },
  () => GetFoundationModelAvailabilityRequest$,
  () => GetFoundationModelAvailabilityResponse$
];
var GetGuardrail$ = [
  9,
  n0,
  _GG,
  { [_ht]: ["GET", "/guardrails/{guardrailIdentifier}", 200] },
  () => GetGuardrailRequest$,
  () => GetGuardrailResponse$
];
var GetImportedModel$ = [
  9,
  n0,
  _GIM,
  { [_ht]: ["GET", "/imported-models/{modelIdentifier}", 200] },
  () => GetImportedModelRequest$,
  () => GetImportedModelResponse$
];
var GetInferenceProfile$ = [
  9,
  n0,
  _GIP,
  { [_ht]: ["GET", "/inference-profiles/{inferenceProfileIdentifier}", 200] },
  () => GetInferenceProfileRequest$,
  () => GetInferenceProfileResponse$
];
var GetMarketplaceModelEndpoint$ = [
  9,
  n0,
  _GMME,
  { [_ht]: ["GET", "/marketplace-model/endpoints/{endpointArn}", 200] },
  () => GetMarketplaceModelEndpointRequest$,
  () => GetMarketplaceModelEndpointResponse$
];
var GetModelCopyJob$ = [
  9,
  n0,
  _GMCJ,
  { [_ht]: ["GET", "/model-copy-jobs/{jobArn}", 200] },
  () => GetModelCopyJobRequest$,
  () => GetModelCopyJobResponse$
];
var GetModelCustomizationJob$ = [
  9,
  n0,
  _GMCJe,
  { [_ht]: ["GET", "/model-customization-jobs/{jobIdentifier}", 200] },
  () => GetModelCustomizationJobRequest$,
  () => GetModelCustomizationJobResponse$
];
var GetModelImportJob$ = [
  9,
  n0,
  _GMIJ,
  { [_ht]: ["GET", "/model-import-jobs/{jobIdentifier}", 200] },
  () => GetModelImportJobRequest$,
  () => GetModelImportJobResponse$
];
var GetModelInvocationJob$ = [
  9,
  n0,
  _GMIJe,
  { [_ht]: ["GET", "/model-invocation-job/{jobIdentifier}", 200] },
  () => GetModelInvocationJobRequest$,
  () => GetModelInvocationJobResponse$
];
var GetModelInvocationLoggingConfiguration$ = [
  9,
  n0,
  _GMILC,
  { [_ht]: ["GET", "/logging/modelinvocations", 200] },
  () => GetModelInvocationLoggingConfigurationRequest$,
  () => GetModelInvocationLoggingConfigurationResponse$
];
var GetPromptRouter$ = [
  9,
  n0,
  _GPR,
  { [_ht]: ["GET", "/prompt-routers/{promptRouterArn}", 200] },
  () => GetPromptRouterRequest$,
  () => GetPromptRouterResponse$
];
var GetProvisionedModelThroughput$ = [
  9,
  n0,
  _GPMT,
  { [_ht]: ["GET", "/provisioned-model-throughput/{provisionedModelId}", 200] },
  () => GetProvisionedModelThroughputRequest$,
  () => GetProvisionedModelThroughputResponse$
];
var GetUseCaseForModelAccess$ = [
  9,
  n0,
  _GUCFMA,
  { [_ht]: ["GET", "/use-case-for-model-access", 200] },
  () => GetUseCaseForModelAccessRequest$,
  () => GetUseCaseForModelAccessResponse$
];
var ListAutomatedReasoningPolicies$ = [
  9,
  n0,
  _LARP,
  { [_ht]: ["GET", "/automated-reasoning-policies", 200] },
  () => ListAutomatedReasoningPoliciesRequest$,
  () => ListAutomatedReasoningPoliciesResponse$
];
var ListAutomatedReasoningPolicyBuildWorkflows$ = [
  9,
  n0,
  _LARPBW,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows", 200] },
  () => ListAutomatedReasoningPolicyBuildWorkflowsRequest$,
  () => ListAutomatedReasoningPolicyBuildWorkflowsResponse$
];
var ListAutomatedReasoningPolicyTestCases$ = [
  9,
  n0,
  _LARPTC,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/test-cases", 200] },
  () => ListAutomatedReasoningPolicyTestCasesRequest$,
  () => ListAutomatedReasoningPolicyTestCasesResponse$
];
var ListAutomatedReasoningPolicyTestResults$ = [
  9,
  n0,
  _LARPTR,
  { [_ht]: ["GET", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/test-results", 200] },
  () => ListAutomatedReasoningPolicyTestResultsRequest$,
  () => ListAutomatedReasoningPolicyTestResultsResponse$
];
var ListCustomModelDeployments$ = [
  9,
  n0,
  _LCMD,
  { [_ht]: ["GET", "/model-customization/custom-model-deployments", 200] },
  () => ListCustomModelDeploymentsRequest$,
  () => ListCustomModelDeploymentsResponse$
];
var ListCustomModels$ = [
  9,
  n0,
  _LCM,
  { [_ht]: ["GET", "/custom-models", 200] },
  () => ListCustomModelsRequest$,
  () => ListCustomModelsResponse$
];
var ListEnforcedGuardrailsConfiguration$ = [
  9,
  n0,
  _LEGC,
  { [_ht]: ["GET", "/enforcedGuardrailsConfiguration", 200] },
  () => ListEnforcedGuardrailsConfigurationRequest$,
  () => ListEnforcedGuardrailsConfigurationResponse$
];
var ListEvaluationJobs$ = [
  9,
  n0,
  _LEJ,
  { [_ht]: ["GET", "/evaluation-jobs", 200] },
  () => ListEvaluationJobsRequest$,
  () => ListEvaluationJobsResponse$
];
var ListFoundationModelAgreementOffers$ = [
  9,
  n0,
  _LFMAO,
  { [_ht]: ["GET", "/list-foundation-model-agreement-offers/{modelId}", 200] },
  () => ListFoundationModelAgreementOffersRequest$,
  () => ListFoundationModelAgreementOffersResponse$
];
var ListFoundationModels$ = [
  9,
  n0,
  _LFM,
  { [_ht]: ["GET", "/foundation-models", 200] },
  () => ListFoundationModelsRequest$,
  () => ListFoundationModelsResponse$
];
var ListGuardrails$ = [
  9,
  n0,
  _LG,
  { [_ht]: ["GET", "/guardrails", 200] },
  () => ListGuardrailsRequest$,
  () => ListGuardrailsResponse$
];
var ListImportedModels$ = [
  9,
  n0,
  _LIM,
  { [_ht]: ["GET", "/imported-models", 200] },
  () => ListImportedModelsRequest$,
  () => ListImportedModelsResponse$
];
var ListInferenceProfiles$ = [
  9,
  n0,
  _LIP,
  { [_ht]: ["GET", "/inference-profiles", 200] },
  () => ListInferenceProfilesRequest$,
  () => ListInferenceProfilesResponse$
];
var ListMarketplaceModelEndpoints$ = [
  9,
  n0,
  _LMME,
  { [_ht]: ["GET", "/marketplace-model/endpoints", 200] },
  () => ListMarketplaceModelEndpointsRequest$,
  () => ListMarketplaceModelEndpointsResponse$
];
var ListModelCopyJobs$ = [
  9,
  n0,
  _LMCJ,
  { [_ht]: ["GET", "/model-copy-jobs", 200] },
  () => ListModelCopyJobsRequest$,
  () => ListModelCopyJobsResponse$
];
var ListModelCustomizationJobs$ = [
  9,
  n0,
  _LMCJi,
  { [_ht]: ["GET", "/model-customization-jobs", 200] },
  () => ListModelCustomizationJobsRequest$,
  () => ListModelCustomizationJobsResponse$
];
var ListModelImportJobs$ = [
  9,
  n0,
  _LMIJ,
  { [_ht]: ["GET", "/model-import-jobs", 200] },
  () => ListModelImportJobsRequest$,
  () => ListModelImportJobsResponse$
];
var ListModelInvocationJobs$ = [
  9,
  n0,
  _LMIJi,
  { [_ht]: ["GET", "/model-invocation-jobs", 200] },
  () => ListModelInvocationJobsRequest$,
  () => ListModelInvocationJobsResponse$
];
var ListPromptRouters$ = [
  9,
  n0,
  _LPR,
  { [_ht]: ["GET", "/prompt-routers", 200] },
  () => ListPromptRoutersRequest$,
  () => ListPromptRoutersResponse$
];
var ListProvisionedModelThroughputs$ = [
  9,
  n0,
  _LPMT,
  { [_ht]: ["GET", "/provisioned-model-throughputs", 200] },
  () => ListProvisionedModelThroughputsRequest$,
  () => ListProvisionedModelThroughputsResponse$
];
var ListTagsForResource$ = [
  9,
  n0,
  _LTFR,
  { [_ht]: ["POST", "/listTagsForResource", 200] },
  () => ListTagsForResourceRequest$,
  () => ListTagsForResourceResponse$
];
var PutEnforcedGuardrailConfiguration$ = [
  9,
  n0,
  _PEGC,
  { [_ht]: ["PUT", "/enforcedGuardrailsConfiguration", 200] },
  () => PutEnforcedGuardrailConfigurationRequest$,
  () => PutEnforcedGuardrailConfigurationResponse$
];
var PutModelInvocationLoggingConfiguration$ = [
  9,
  n0,
  _PMILC,
  { [_ht]: ["PUT", "/logging/modelinvocations", 200] },
  () => PutModelInvocationLoggingConfigurationRequest$,
  () => PutModelInvocationLoggingConfigurationResponse$
];
var PutUseCaseForModelAccess$ = [
  9,
  n0,
  _PUCFMA,
  { [_ht]: ["POST", "/use-case-for-model-access", 201] },
  () => PutUseCaseForModelAccessRequest$,
  () => PutUseCaseForModelAccessResponse$
];
var RegisterMarketplaceModelEndpoint$ = [
  9,
  n0,
  _RMME,
  { [_ht]: ["POST", "/marketplace-model/endpoints/{endpointIdentifier}/registration", 200] },
  () => RegisterMarketplaceModelEndpointRequest$,
  () => RegisterMarketplaceModelEndpointResponse$
];
var StartAutomatedReasoningPolicyBuildWorkflow$ = [
  9,
  n0,
  _SARPBW,
  { [_ht]: ["POST", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowType}/start", 200] },
  () => StartAutomatedReasoningPolicyBuildWorkflowRequest$,
  () => StartAutomatedReasoningPolicyBuildWorkflowResponse$
];
var StartAutomatedReasoningPolicyTestWorkflow$ = [
  9,
  n0,
  _SARPTW,
  { [_ht]: ["POST", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/test-workflows", 200] },
  () => StartAutomatedReasoningPolicyTestWorkflowRequest$,
  () => StartAutomatedReasoningPolicyTestWorkflowResponse$
];
var StopEvaluationJob$ = [
  9,
  n0,
  _SEJ,
  { [_ht]: ["POST", "/evaluation-job/{jobIdentifier}/stop", 200] },
  () => StopEvaluationJobRequest$,
  () => StopEvaluationJobResponse$
];
var StopModelCustomizationJob$ = [
  9,
  n0,
  _SMCJ,
  { [_ht]: ["POST", "/model-customization-jobs/{jobIdentifier}/stop", 200] },
  () => StopModelCustomizationJobRequest$,
  () => StopModelCustomizationJobResponse$
];
var StopModelInvocationJob$ = [
  9,
  n0,
  _SMIJ,
  { [_ht]: ["POST", "/model-invocation-job/{jobIdentifier}/stop", 200] },
  () => StopModelInvocationJobRequest$,
  () => StopModelInvocationJobResponse$
];
var TagResource$ = [
  9,
  n0,
  _TR,
  { [_ht]: ["POST", "/tagResource", 200] },
  () => TagResourceRequest$,
  () => TagResourceResponse$
];
var UntagResource$ = [
  9,
  n0,
  _UR,
  { [_ht]: ["POST", "/untagResource", 200] },
  () => UntagResourceRequest$,
  () => UntagResourceResponse$
];
var UpdateAutomatedReasoningPolicy$ = [
  9,
  n0,
  _UARP,
  { [_ht]: ["PATCH", "/automated-reasoning-policies/{policyArn}", 200] },
  () => UpdateAutomatedReasoningPolicyRequest$,
  () => UpdateAutomatedReasoningPolicyResponse$
];
var UpdateAutomatedReasoningPolicyAnnotations$ = [
  9,
  n0,
  _UARPA,
  { [_ht]: ["PATCH", "/automated-reasoning-policies/{policyArn}/build-workflows/{buildWorkflowId}/annotations", 200] },
  () => UpdateAutomatedReasoningPolicyAnnotationsRequest$,
  () => UpdateAutomatedReasoningPolicyAnnotationsResponse$
];
var UpdateAutomatedReasoningPolicyTestCase$ = [
  9,
  n0,
  _UARPTC,
  { [_ht]: ["PATCH", "/automated-reasoning-policies/{policyArn}/test-cases/{testCaseId}", 200] },
  () => UpdateAutomatedReasoningPolicyTestCaseRequest$,
  () => UpdateAutomatedReasoningPolicyTestCaseResponse$
];
var UpdateCustomModelDeployment$ = [
  9,
  n0,
  _UCMD,
  { [_ht]: ["PATCH", "/model-customization/custom-model-deployments/{customModelDeploymentIdentifier}", 202] },
  () => UpdateCustomModelDeploymentRequest$,
  () => UpdateCustomModelDeploymentResponse$
];
var UpdateGuardrail$ = [
  9,
  n0,
  _UG,
  { [_ht]: ["PUT", "/guardrails/{guardrailIdentifier}", 202] },
  () => UpdateGuardrailRequest$,
  () => UpdateGuardrailResponse$
];
var UpdateMarketplaceModelEndpoint$ = [
  9,
  n0,
  _UMME,
  { [_ht]: ["PATCH", "/marketplace-model/endpoints/{endpointArn}", 200] },
  () => UpdateMarketplaceModelEndpointRequest$,
  () => UpdateMarketplaceModelEndpointResponse$
];
var UpdateProvisionedModelThroughput$ = [
  9,
  n0,
  _UPMT,
  { [_ht]: ["PATCH", "/provisioned-model-throughput/{provisionedModelId}", 200] },
  () => UpdateProvisionedModelThroughputRequest$,
  () => UpdateProvisionedModelThroughputResponse$
];

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/BatchDeleteEvaluationJobCommand.js
var BatchDeleteEvaluationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "BatchDeleteEvaluationJob", {}).n("BedrockClient", "BatchDeleteEvaluationJobCommand").sc(BatchDeleteEvaluationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CancelAutomatedReasoningPolicyBuildWorkflowCommand.js
var CancelAutomatedReasoningPolicyBuildWorkflowCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CancelAutomatedReasoningPolicyBuildWorkflow", {}).n("BedrockClient", "CancelAutomatedReasoningPolicyBuildWorkflowCommand").sc(CancelAutomatedReasoningPolicyBuildWorkflow$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateAutomatedReasoningPolicyCommand.js
var CreateAutomatedReasoningPolicyCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateAutomatedReasoningPolicy", {}).n("BedrockClient", "CreateAutomatedReasoningPolicyCommand").sc(CreateAutomatedReasoningPolicy$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateAutomatedReasoningPolicyTestCaseCommand.js
var CreateAutomatedReasoningPolicyTestCaseCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateAutomatedReasoningPolicyTestCase", {}).n("BedrockClient", "CreateAutomatedReasoningPolicyTestCaseCommand").sc(CreateAutomatedReasoningPolicyTestCase$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateAutomatedReasoningPolicyVersionCommand.js
var CreateAutomatedReasoningPolicyVersionCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateAutomatedReasoningPolicyVersion", {}).n("BedrockClient", "CreateAutomatedReasoningPolicyVersionCommand").sc(CreateAutomatedReasoningPolicyVersion$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateCustomModelCommand.js
var CreateCustomModelCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateCustomModel", {}).n("BedrockClient", "CreateCustomModelCommand").sc(CreateCustomModel$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateCustomModelDeploymentCommand.js
var CreateCustomModelDeploymentCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateCustomModelDeployment", {}).n("BedrockClient", "CreateCustomModelDeploymentCommand").sc(CreateCustomModelDeployment$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateEvaluationJobCommand.js
var CreateEvaluationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateEvaluationJob", {}).n("BedrockClient", "CreateEvaluationJobCommand").sc(CreateEvaluationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateFoundationModelAgreementCommand.js
var CreateFoundationModelAgreementCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateFoundationModelAgreement", {}).n("BedrockClient", "CreateFoundationModelAgreementCommand").sc(CreateFoundationModelAgreement$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateGuardrailCommand.js
var CreateGuardrailCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateGuardrail", {}).n("BedrockClient", "CreateGuardrailCommand").sc(CreateGuardrail$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateGuardrailVersionCommand.js
var CreateGuardrailVersionCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateGuardrailVersion", {}).n("BedrockClient", "CreateGuardrailVersionCommand").sc(CreateGuardrailVersion$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateInferenceProfileCommand.js
var CreateInferenceProfileCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateInferenceProfile", {}).n("BedrockClient", "CreateInferenceProfileCommand").sc(CreateInferenceProfile$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateMarketplaceModelEndpointCommand.js
var CreateMarketplaceModelEndpointCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateMarketplaceModelEndpoint", {}).n("BedrockClient", "CreateMarketplaceModelEndpointCommand").sc(CreateMarketplaceModelEndpoint$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateModelCopyJobCommand.js
var CreateModelCopyJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateModelCopyJob", {}).n("BedrockClient", "CreateModelCopyJobCommand").sc(CreateModelCopyJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateModelCustomizationJobCommand.js
var CreateModelCustomizationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateModelCustomizationJob", {}).n("BedrockClient", "CreateModelCustomizationJobCommand").sc(CreateModelCustomizationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateModelImportJobCommand.js
var CreateModelImportJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateModelImportJob", {}).n("BedrockClient", "CreateModelImportJobCommand").sc(CreateModelImportJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateModelInvocationJobCommand.js
var CreateModelInvocationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateModelInvocationJob", {}).n("BedrockClient", "CreateModelInvocationJobCommand").sc(CreateModelInvocationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreatePromptRouterCommand.js
var CreatePromptRouterCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreatePromptRouter", {}).n("BedrockClient", "CreatePromptRouterCommand").sc(CreatePromptRouter$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/CreateProvisionedModelThroughputCommand.js
var CreateProvisionedModelThroughputCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "CreateProvisionedModelThroughput", {}).n("BedrockClient", "CreateProvisionedModelThroughputCommand").sc(CreateProvisionedModelThroughput$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteAutomatedReasoningPolicyBuildWorkflowCommand.js
var DeleteAutomatedReasoningPolicyBuildWorkflowCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteAutomatedReasoningPolicyBuildWorkflow", {}).n("BedrockClient", "DeleteAutomatedReasoningPolicyBuildWorkflowCommand").sc(DeleteAutomatedReasoningPolicyBuildWorkflow$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteAutomatedReasoningPolicyCommand.js
var DeleteAutomatedReasoningPolicyCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteAutomatedReasoningPolicy", {}).n("BedrockClient", "DeleteAutomatedReasoningPolicyCommand").sc(DeleteAutomatedReasoningPolicy$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteAutomatedReasoningPolicyTestCaseCommand.js
var DeleteAutomatedReasoningPolicyTestCaseCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteAutomatedReasoningPolicyTestCase", {}).n("BedrockClient", "DeleteAutomatedReasoningPolicyTestCaseCommand").sc(DeleteAutomatedReasoningPolicyTestCase$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteCustomModelCommand.js
var DeleteCustomModelCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteCustomModel", {}).n("BedrockClient", "DeleteCustomModelCommand").sc(DeleteCustomModel$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteCustomModelDeploymentCommand.js
var DeleteCustomModelDeploymentCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteCustomModelDeployment", {}).n("BedrockClient", "DeleteCustomModelDeploymentCommand").sc(DeleteCustomModelDeployment$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteEnforcedGuardrailConfigurationCommand.js
var DeleteEnforcedGuardrailConfigurationCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteEnforcedGuardrailConfiguration", {}).n("BedrockClient", "DeleteEnforcedGuardrailConfigurationCommand").sc(DeleteEnforcedGuardrailConfiguration$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteFoundationModelAgreementCommand.js
var DeleteFoundationModelAgreementCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteFoundationModelAgreement", {}).n("BedrockClient", "DeleteFoundationModelAgreementCommand").sc(DeleteFoundationModelAgreement$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteGuardrailCommand.js
var DeleteGuardrailCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteGuardrail", {}).n("BedrockClient", "DeleteGuardrailCommand").sc(DeleteGuardrail$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteImportedModelCommand.js
var DeleteImportedModelCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteImportedModel", {}).n("BedrockClient", "DeleteImportedModelCommand").sc(DeleteImportedModel$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteInferenceProfileCommand.js
var DeleteInferenceProfileCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteInferenceProfile", {}).n("BedrockClient", "DeleteInferenceProfileCommand").sc(DeleteInferenceProfile$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteMarketplaceModelEndpointCommand.js
var DeleteMarketplaceModelEndpointCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteMarketplaceModelEndpoint", {}).n("BedrockClient", "DeleteMarketplaceModelEndpointCommand").sc(DeleteMarketplaceModelEndpoint$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteModelInvocationLoggingConfigurationCommand.js
var DeleteModelInvocationLoggingConfigurationCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteModelInvocationLoggingConfiguration", {}).n("BedrockClient", "DeleteModelInvocationLoggingConfigurationCommand").sc(DeleteModelInvocationLoggingConfiguration$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeletePromptRouterCommand.js
var DeletePromptRouterCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeletePromptRouter", {}).n("BedrockClient", "DeletePromptRouterCommand").sc(DeletePromptRouter$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeleteProvisionedModelThroughputCommand.js
var DeleteProvisionedModelThroughputCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeleteProvisionedModelThroughput", {}).n("BedrockClient", "DeleteProvisionedModelThroughputCommand").sc(DeleteProvisionedModelThroughput$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/DeregisterMarketplaceModelEndpointCommand.js
var DeregisterMarketplaceModelEndpointCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "DeregisterMarketplaceModelEndpoint", {}).n("BedrockClient", "DeregisterMarketplaceModelEndpointCommand").sc(DeregisterMarketplaceModelEndpoint$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ExportAutomatedReasoningPolicyVersionCommand.js
var ExportAutomatedReasoningPolicyVersionCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ExportAutomatedReasoningPolicyVersion", {}).n("BedrockClient", "ExportAutomatedReasoningPolicyVersionCommand").sc(ExportAutomatedReasoningPolicyVersion$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyAnnotationsCommand.js
var GetAutomatedReasoningPolicyAnnotationsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicyAnnotations", {}).n("BedrockClient", "GetAutomatedReasoningPolicyAnnotationsCommand").sc(GetAutomatedReasoningPolicyAnnotations$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyBuildWorkflowCommand.js
var GetAutomatedReasoningPolicyBuildWorkflowCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicyBuildWorkflow", {}).n("BedrockClient", "GetAutomatedReasoningPolicyBuildWorkflowCommand").sc(GetAutomatedReasoningPolicyBuildWorkflow$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyBuildWorkflowResultAssetsCommand.js
var GetAutomatedReasoningPolicyBuildWorkflowResultAssetsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicyBuildWorkflowResultAssets", {}).n("BedrockClient", "GetAutomatedReasoningPolicyBuildWorkflowResultAssetsCommand").sc(GetAutomatedReasoningPolicyBuildWorkflowResultAssets$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyCommand.js
var GetAutomatedReasoningPolicyCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicy", {}).n("BedrockClient", "GetAutomatedReasoningPolicyCommand").sc(GetAutomatedReasoningPolicy$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyNextScenarioCommand.js
var GetAutomatedReasoningPolicyNextScenarioCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicyNextScenario", {}).n("BedrockClient", "GetAutomatedReasoningPolicyNextScenarioCommand").sc(GetAutomatedReasoningPolicyNextScenario$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyTestCaseCommand.js
var GetAutomatedReasoningPolicyTestCaseCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicyTestCase", {}).n("BedrockClient", "GetAutomatedReasoningPolicyTestCaseCommand").sc(GetAutomatedReasoningPolicyTestCase$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetAutomatedReasoningPolicyTestResultCommand.js
var GetAutomatedReasoningPolicyTestResultCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetAutomatedReasoningPolicyTestResult", {}).n("BedrockClient", "GetAutomatedReasoningPolicyTestResultCommand").sc(GetAutomatedReasoningPolicyTestResult$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetCustomModelCommand.js
var GetCustomModelCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetCustomModel", {}).n("BedrockClient", "GetCustomModelCommand").sc(GetCustomModel$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetCustomModelDeploymentCommand.js
var GetCustomModelDeploymentCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetCustomModelDeployment", {}).n("BedrockClient", "GetCustomModelDeploymentCommand").sc(GetCustomModelDeployment$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetEvaluationJobCommand.js
var GetEvaluationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetEvaluationJob", {}).n("BedrockClient", "GetEvaluationJobCommand").sc(GetEvaluationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetFoundationModelAvailabilityCommand.js
var GetFoundationModelAvailabilityCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetFoundationModelAvailability", {}).n("BedrockClient", "GetFoundationModelAvailabilityCommand").sc(GetFoundationModelAvailability$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetFoundationModelCommand.js
var GetFoundationModelCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetFoundationModel", {}).n("BedrockClient", "GetFoundationModelCommand").sc(GetFoundationModel$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetGuardrailCommand.js
var GetGuardrailCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetGuardrail", {}).n("BedrockClient", "GetGuardrailCommand").sc(GetGuardrail$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetImportedModelCommand.js
var GetImportedModelCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetImportedModel", {}).n("BedrockClient", "GetImportedModelCommand").sc(GetImportedModel$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetInferenceProfileCommand.js
var GetInferenceProfileCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetInferenceProfile", {}).n("BedrockClient", "GetInferenceProfileCommand").sc(GetInferenceProfile$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetMarketplaceModelEndpointCommand.js
var GetMarketplaceModelEndpointCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetMarketplaceModelEndpoint", {}).n("BedrockClient", "GetMarketplaceModelEndpointCommand").sc(GetMarketplaceModelEndpoint$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetModelCopyJobCommand.js
var GetModelCopyJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetModelCopyJob", {}).n("BedrockClient", "GetModelCopyJobCommand").sc(GetModelCopyJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetModelCustomizationJobCommand.js
var GetModelCustomizationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetModelCustomizationJob", {}).n("BedrockClient", "GetModelCustomizationJobCommand").sc(GetModelCustomizationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetModelImportJobCommand.js
var GetModelImportJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetModelImportJob", {}).n("BedrockClient", "GetModelImportJobCommand").sc(GetModelImportJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetModelInvocationJobCommand.js
var GetModelInvocationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetModelInvocationJob", {}).n("BedrockClient", "GetModelInvocationJobCommand").sc(GetModelInvocationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetModelInvocationLoggingConfigurationCommand.js
var GetModelInvocationLoggingConfigurationCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetModelInvocationLoggingConfiguration", {}).n("BedrockClient", "GetModelInvocationLoggingConfigurationCommand").sc(GetModelInvocationLoggingConfiguration$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetPromptRouterCommand.js
var GetPromptRouterCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetPromptRouter", {}).n("BedrockClient", "GetPromptRouterCommand").sc(GetPromptRouter$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetProvisionedModelThroughputCommand.js
var GetProvisionedModelThroughputCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetProvisionedModelThroughput", {}).n("BedrockClient", "GetProvisionedModelThroughputCommand").sc(GetProvisionedModelThroughput$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/GetUseCaseForModelAccessCommand.js
var GetUseCaseForModelAccessCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "GetUseCaseForModelAccess", {}).n("BedrockClient", "GetUseCaseForModelAccessCommand").sc(GetUseCaseForModelAccess$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListAutomatedReasoningPoliciesCommand.js
var ListAutomatedReasoningPoliciesCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListAutomatedReasoningPolicies", {}).n("BedrockClient", "ListAutomatedReasoningPoliciesCommand").sc(ListAutomatedReasoningPolicies$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListAutomatedReasoningPolicyBuildWorkflowsCommand.js
var ListAutomatedReasoningPolicyBuildWorkflowsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListAutomatedReasoningPolicyBuildWorkflows", {}).n("BedrockClient", "ListAutomatedReasoningPolicyBuildWorkflowsCommand").sc(ListAutomatedReasoningPolicyBuildWorkflows$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListAutomatedReasoningPolicyTestCasesCommand.js
var ListAutomatedReasoningPolicyTestCasesCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListAutomatedReasoningPolicyTestCases", {}).n("BedrockClient", "ListAutomatedReasoningPolicyTestCasesCommand").sc(ListAutomatedReasoningPolicyTestCases$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListAutomatedReasoningPolicyTestResultsCommand.js
var ListAutomatedReasoningPolicyTestResultsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListAutomatedReasoningPolicyTestResults", {}).n("BedrockClient", "ListAutomatedReasoningPolicyTestResultsCommand").sc(ListAutomatedReasoningPolicyTestResults$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListCustomModelDeploymentsCommand.js
var ListCustomModelDeploymentsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListCustomModelDeployments", {}).n("BedrockClient", "ListCustomModelDeploymentsCommand").sc(ListCustomModelDeployments$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListCustomModelsCommand.js
var ListCustomModelsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListCustomModels", {}).n("BedrockClient", "ListCustomModelsCommand").sc(ListCustomModels$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListEnforcedGuardrailsConfigurationCommand.js
var ListEnforcedGuardrailsConfigurationCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListEnforcedGuardrailsConfiguration", {}).n("BedrockClient", "ListEnforcedGuardrailsConfigurationCommand").sc(ListEnforcedGuardrailsConfiguration$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListEvaluationJobsCommand.js
var ListEvaluationJobsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListEvaluationJobs", {}).n("BedrockClient", "ListEvaluationJobsCommand").sc(ListEvaluationJobs$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListFoundationModelAgreementOffersCommand.js
var ListFoundationModelAgreementOffersCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListFoundationModelAgreementOffers", {}).n("BedrockClient", "ListFoundationModelAgreementOffersCommand").sc(ListFoundationModelAgreementOffers$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListFoundationModelsCommand.js
var ListFoundationModelsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListFoundationModels", {}).n("BedrockClient", "ListFoundationModelsCommand").sc(ListFoundationModels$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListGuardrailsCommand.js
var ListGuardrailsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListGuardrails", {}).n("BedrockClient", "ListGuardrailsCommand").sc(ListGuardrails$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListImportedModelsCommand.js
var ListImportedModelsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListImportedModels", {}).n("BedrockClient", "ListImportedModelsCommand").sc(ListImportedModels$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListInferenceProfilesCommand.js
var ListInferenceProfilesCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListInferenceProfiles", {}).n("BedrockClient", "ListInferenceProfilesCommand").sc(ListInferenceProfiles$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListMarketplaceModelEndpointsCommand.js
var ListMarketplaceModelEndpointsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListMarketplaceModelEndpoints", {}).n("BedrockClient", "ListMarketplaceModelEndpointsCommand").sc(ListMarketplaceModelEndpoints$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListModelCopyJobsCommand.js
var ListModelCopyJobsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListModelCopyJobs", {}).n("BedrockClient", "ListModelCopyJobsCommand").sc(ListModelCopyJobs$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListModelCustomizationJobsCommand.js
var ListModelCustomizationJobsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListModelCustomizationJobs", {}).n("BedrockClient", "ListModelCustomizationJobsCommand").sc(ListModelCustomizationJobs$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListModelImportJobsCommand.js
var ListModelImportJobsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListModelImportJobs", {}).n("BedrockClient", "ListModelImportJobsCommand").sc(ListModelImportJobs$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListModelInvocationJobsCommand.js
var ListModelInvocationJobsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListModelInvocationJobs", {}).n("BedrockClient", "ListModelInvocationJobsCommand").sc(ListModelInvocationJobs$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListPromptRoutersCommand.js
var ListPromptRoutersCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListPromptRouters", {}).n("BedrockClient", "ListPromptRoutersCommand").sc(ListPromptRouters$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListProvisionedModelThroughputsCommand.js
var ListProvisionedModelThroughputsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListProvisionedModelThroughputs", {}).n("BedrockClient", "ListProvisionedModelThroughputsCommand").sc(ListProvisionedModelThroughputs$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/ListTagsForResourceCommand.js
var ListTagsForResourceCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "ListTagsForResource", {}).n("BedrockClient", "ListTagsForResourceCommand").sc(ListTagsForResource$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/PutEnforcedGuardrailConfigurationCommand.js
var PutEnforcedGuardrailConfigurationCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "PutEnforcedGuardrailConfiguration", {}).n("BedrockClient", "PutEnforcedGuardrailConfigurationCommand").sc(PutEnforcedGuardrailConfiguration$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/PutModelInvocationLoggingConfigurationCommand.js
var PutModelInvocationLoggingConfigurationCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "PutModelInvocationLoggingConfiguration", {}).n("BedrockClient", "PutModelInvocationLoggingConfigurationCommand").sc(PutModelInvocationLoggingConfiguration$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/PutUseCaseForModelAccessCommand.js
var PutUseCaseForModelAccessCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "PutUseCaseForModelAccess", {}).n("BedrockClient", "PutUseCaseForModelAccessCommand").sc(PutUseCaseForModelAccess$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/RegisterMarketplaceModelEndpointCommand.js
var RegisterMarketplaceModelEndpointCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "RegisterMarketplaceModelEndpoint", {}).n("BedrockClient", "RegisterMarketplaceModelEndpointCommand").sc(RegisterMarketplaceModelEndpoint$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/StartAutomatedReasoningPolicyBuildWorkflowCommand.js
var StartAutomatedReasoningPolicyBuildWorkflowCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "StartAutomatedReasoningPolicyBuildWorkflow", {}).n("BedrockClient", "StartAutomatedReasoningPolicyBuildWorkflowCommand").sc(StartAutomatedReasoningPolicyBuildWorkflow$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/StartAutomatedReasoningPolicyTestWorkflowCommand.js
var StartAutomatedReasoningPolicyTestWorkflowCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "StartAutomatedReasoningPolicyTestWorkflow", {}).n("BedrockClient", "StartAutomatedReasoningPolicyTestWorkflowCommand").sc(StartAutomatedReasoningPolicyTestWorkflow$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/StopEvaluationJobCommand.js
var StopEvaluationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "StopEvaluationJob", {}).n("BedrockClient", "StopEvaluationJobCommand").sc(StopEvaluationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/StopModelCustomizationJobCommand.js
var StopModelCustomizationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "StopModelCustomizationJob", {}).n("BedrockClient", "StopModelCustomizationJobCommand").sc(StopModelCustomizationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/StopModelInvocationJobCommand.js
var StopModelInvocationJobCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "StopModelInvocationJob", {}).n("BedrockClient", "StopModelInvocationJobCommand").sc(StopModelInvocationJob$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/TagResourceCommand.js
var TagResourceCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "TagResource", {}).n("BedrockClient", "TagResourceCommand").sc(TagResource$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UntagResourceCommand.js
var UntagResourceCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UntagResource", {}).n("BedrockClient", "UntagResourceCommand").sc(UntagResource$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateAutomatedReasoningPolicyAnnotationsCommand.js
var UpdateAutomatedReasoningPolicyAnnotationsCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateAutomatedReasoningPolicyAnnotations", {}).n("BedrockClient", "UpdateAutomatedReasoningPolicyAnnotationsCommand").sc(UpdateAutomatedReasoningPolicyAnnotations$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateAutomatedReasoningPolicyCommand.js
var UpdateAutomatedReasoningPolicyCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateAutomatedReasoningPolicy", {}).n("BedrockClient", "UpdateAutomatedReasoningPolicyCommand").sc(UpdateAutomatedReasoningPolicy$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateAutomatedReasoningPolicyTestCaseCommand.js
var UpdateAutomatedReasoningPolicyTestCaseCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateAutomatedReasoningPolicyTestCase", {}).n("BedrockClient", "UpdateAutomatedReasoningPolicyTestCaseCommand").sc(UpdateAutomatedReasoningPolicyTestCase$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateCustomModelDeploymentCommand.js
var UpdateCustomModelDeploymentCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateCustomModelDeployment", {}).n("BedrockClient", "UpdateCustomModelDeploymentCommand").sc(UpdateCustomModelDeployment$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateGuardrailCommand.js
var UpdateGuardrailCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateGuardrail", {}).n("BedrockClient", "UpdateGuardrailCommand").sc(UpdateGuardrail$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateMarketplaceModelEndpointCommand.js
var UpdateMarketplaceModelEndpointCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateMarketplaceModelEndpoint", {}).n("BedrockClient", "UpdateMarketplaceModelEndpointCommand").sc(UpdateMarketplaceModelEndpoint$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/commands/UpdateProvisionedModelThroughputCommand.js
var UpdateProvisionedModelThroughputCommand = class extends Command.classBuilder().ep(commonParams).m(function(Command2, cs, config, o2) {
  return [getEndpointPlugin(config, Command2.getEndpointParameterInstructions())];
}).s("AmazonBedrockControlPlaneService", "UpdateProvisionedModelThroughput", {}).n("BedrockClient", "UpdateProvisionedModelThroughputCommand").sc(UpdateProvisionedModelThroughput$).build() {
};

// node_modules/@aws-sdk/client-bedrock/dist-es/Bedrock.js
var commands = {
  BatchDeleteEvaluationJobCommand,
  CancelAutomatedReasoningPolicyBuildWorkflowCommand,
  CreateAutomatedReasoningPolicyCommand,
  CreateAutomatedReasoningPolicyTestCaseCommand,
  CreateAutomatedReasoningPolicyVersionCommand,
  CreateCustomModelCommand,
  CreateCustomModelDeploymentCommand,
  CreateEvaluationJobCommand,
  CreateFoundationModelAgreementCommand,
  CreateGuardrailCommand,
  CreateGuardrailVersionCommand,
  CreateInferenceProfileCommand,
  CreateMarketplaceModelEndpointCommand,
  CreateModelCopyJobCommand,
  CreateModelCustomizationJobCommand,
  CreateModelImportJobCommand,
  CreateModelInvocationJobCommand,
  CreatePromptRouterCommand,
  CreateProvisionedModelThroughputCommand,
  DeleteAutomatedReasoningPolicyCommand,
  DeleteAutomatedReasoningPolicyBuildWorkflowCommand,
  DeleteAutomatedReasoningPolicyTestCaseCommand,
  DeleteCustomModelCommand,
  DeleteCustomModelDeploymentCommand,
  DeleteEnforcedGuardrailConfigurationCommand,
  DeleteFoundationModelAgreementCommand,
  DeleteGuardrailCommand,
  DeleteImportedModelCommand,
  DeleteInferenceProfileCommand,
  DeleteMarketplaceModelEndpointCommand,
  DeleteModelInvocationLoggingConfigurationCommand,
  DeletePromptRouterCommand,
  DeleteProvisionedModelThroughputCommand,
  DeregisterMarketplaceModelEndpointCommand,
  ExportAutomatedReasoningPolicyVersionCommand,
  GetAutomatedReasoningPolicyCommand,
  GetAutomatedReasoningPolicyAnnotationsCommand,
  GetAutomatedReasoningPolicyBuildWorkflowCommand,
  GetAutomatedReasoningPolicyBuildWorkflowResultAssetsCommand,
  GetAutomatedReasoningPolicyNextScenarioCommand,
  GetAutomatedReasoningPolicyTestCaseCommand,
  GetAutomatedReasoningPolicyTestResultCommand,
  GetCustomModelCommand,
  GetCustomModelDeploymentCommand,
  GetEvaluationJobCommand,
  GetFoundationModelCommand,
  GetFoundationModelAvailabilityCommand,
  GetGuardrailCommand,
  GetImportedModelCommand,
  GetInferenceProfileCommand,
  GetMarketplaceModelEndpointCommand,
  GetModelCopyJobCommand,
  GetModelCustomizationJobCommand,
  GetModelImportJobCommand,
  GetModelInvocationJobCommand,
  GetModelInvocationLoggingConfigurationCommand,
  GetPromptRouterCommand,
  GetProvisionedModelThroughputCommand,
  GetUseCaseForModelAccessCommand,
  ListAutomatedReasoningPoliciesCommand,
  ListAutomatedReasoningPolicyBuildWorkflowsCommand,
  ListAutomatedReasoningPolicyTestCasesCommand,
  ListAutomatedReasoningPolicyTestResultsCommand,
  ListCustomModelDeploymentsCommand,
  ListCustomModelsCommand,
  ListEnforcedGuardrailsConfigurationCommand,
  ListEvaluationJobsCommand,
  ListFoundationModelAgreementOffersCommand,
  ListFoundationModelsCommand,
  ListGuardrailsCommand,
  ListImportedModelsCommand,
  ListInferenceProfilesCommand,
  ListMarketplaceModelEndpointsCommand,
  ListModelCopyJobsCommand,
  ListModelCustomizationJobsCommand,
  ListModelImportJobsCommand,
  ListModelInvocationJobsCommand,
  ListPromptRoutersCommand,
  ListProvisionedModelThroughputsCommand,
  ListTagsForResourceCommand,
  PutEnforcedGuardrailConfigurationCommand,
  PutModelInvocationLoggingConfigurationCommand,
  PutUseCaseForModelAccessCommand,
  RegisterMarketplaceModelEndpointCommand,
  StartAutomatedReasoningPolicyBuildWorkflowCommand,
  StartAutomatedReasoningPolicyTestWorkflowCommand,
  StopEvaluationJobCommand,
  StopModelCustomizationJobCommand,
  StopModelInvocationJobCommand,
  TagResourceCommand,
  UntagResourceCommand,
  UpdateAutomatedReasoningPolicyCommand,
  UpdateAutomatedReasoningPolicyAnnotationsCommand,
  UpdateAutomatedReasoningPolicyTestCaseCommand,
  UpdateCustomModelDeploymentCommand,
  UpdateGuardrailCommand,
  UpdateMarketplaceModelEndpointCommand,
  UpdateProvisionedModelThroughputCommand
};
var Bedrock = class extends BedrockClient {
};
createAggregatedClient(commands, Bedrock);

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListAutomatedReasoningPoliciesPaginator.js
var paginateListAutomatedReasoningPolicies = createPaginator(BedrockClient, ListAutomatedReasoningPoliciesCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListAutomatedReasoningPolicyBuildWorkflowsPaginator.js
var paginateListAutomatedReasoningPolicyBuildWorkflows = createPaginator(BedrockClient, ListAutomatedReasoningPolicyBuildWorkflowsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListAutomatedReasoningPolicyTestCasesPaginator.js
var paginateListAutomatedReasoningPolicyTestCases = createPaginator(BedrockClient, ListAutomatedReasoningPolicyTestCasesCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListAutomatedReasoningPolicyTestResultsPaginator.js
var paginateListAutomatedReasoningPolicyTestResults = createPaginator(BedrockClient, ListAutomatedReasoningPolicyTestResultsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListCustomModelDeploymentsPaginator.js
var paginateListCustomModelDeployments = createPaginator(BedrockClient, ListCustomModelDeploymentsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListCustomModelsPaginator.js
var paginateListCustomModels = createPaginator(BedrockClient, ListCustomModelsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListEnforcedGuardrailsConfigurationPaginator.js
var paginateListEnforcedGuardrailsConfiguration = createPaginator(BedrockClient, ListEnforcedGuardrailsConfigurationCommand, "nextToken", "nextToken", "");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListEvaluationJobsPaginator.js
var paginateListEvaluationJobs = createPaginator(BedrockClient, ListEvaluationJobsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListGuardrailsPaginator.js
var paginateListGuardrails = createPaginator(BedrockClient, ListGuardrailsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListImportedModelsPaginator.js
var paginateListImportedModels = createPaginator(BedrockClient, ListImportedModelsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListInferenceProfilesPaginator.js
var paginateListInferenceProfiles = createPaginator(BedrockClient, ListInferenceProfilesCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListMarketplaceModelEndpointsPaginator.js
var paginateListMarketplaceModelEndpoints = createPaginator(BedrockClient, ListMarketplaceModelEndpointsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListModelCopyJobsPaginator.js
var paginateListModelCopyJobs = createPaginator(BedrockClient, ListModelCopyJobsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListModelCustomizationJobsPaginator.js
var paginateListModelCustomizationJobs = createPaginator(BedrockClient, ListModelCustomizationJobsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListModelImportJobsPaginator.js
var paginateListModelImportJobs = createPaginator(BedrockClient, ListModelImportJobsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListModelInvocationJobsPaginator.js
var paginateListModelInvocationJobs = createPaginator(BedrockClient, ListModelInvocationJobsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListPromptRoutersPaginator.js
var paginateListPromptRouters = createPaginator(BedrockClient, ListPromptRoutersCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/pagination/ListProvisionedModelThroughputsPaginator.js
var paginateListProvisionedModelThroughputs = createPaginator(BedrockClient, ListProvisionedModelThroughputsCommand, "nextToken", "nextToken", "maxResults");

// node_modules/@aws-sdk/client-bedrock/dist-es/models/enums.js
var InputTags = {
  HONOR: "HONOR",
  IGNORE: "IGNORE"
};
var ConfigurationOwner = {
  ACCOUNT: "ACCOUNT"
};
var AgreementStatus = {
  AVAILABLE: "AVAILABLE",
  ERROR: "ERROR",
  NOT_AVAILABLE: "NOT_AVAILABLE",
  PENDING: "PENDING"
};
var AutomatedReasoningCheckResult = {
  IMPOSSIBLE: "IMPOSSIBLE",
  INVALID: "INVALID",
  NO_TRANSLATION: "NO_TRANSLATION",
  SATISFIABLE: "SATISFIABLE",
  TOO_COMPLEX: "TOO_COMPLEX",
  TRANSLATION_AMBIGUOUS: "TRANSLATION_AMBIGUOUS",
  VALID: "VALID"
};
var AutomatedReasoningPolicyBuildWorkflowType = {
  IMPORT_POLICY: "IMPORT_POLICY",
  INGEST_CONTENT: "INGEST_CONTENT",
  REFINE_POLICY: "REFINE_POLICY"
};
var AutomatedReasoningPolicyBuildDocumentContentType = {
  PDF: "pdf",
  TEXT: "txt"
};
var AutomatedReasoningPolicyBuildWorkflowStatus = {
  BUILDING: "BUILDING",
  CANCELLED: "CANCELLED",
  CANCEL_REQUESTED: "CANCEL_REQUESTED",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  PREPROCESSING: "PREPROCESSING",
  SCHEDULED: "SCHEDULED",
  TESTING: "TESTING"
};
var AutomatedReasoningPolicyBuildResultAssetType = {
  BUILD_LOG: "BUILD_LOG",
  GENERATED_TEST_CASES: "GENERATED_TEST_CASES",
  POLICY_DEFINITION: "POLICY_DEFINITION",
  POLICY_SCENARIOS: "POLICY_SCENARIOS",
  QUALITY_REPORT: "QUALITY_REPORT"
};
var AutomatedReasoningPolicyBuildMessageType = {
  ERROR: "ERROR",
  INFO: "INFO",
  WARNING: "WARNING"
};
var AutomatedReasoningPolicyAnnotationStatus = {
  APPLIED: "APPLIED",
  FAILED: "FAILED"
};
var AutomatedReasoningCheckLogicWarningType = {
  ALWAYS_FALSE: "ALWAYS_FALSE",
  ALWAYS_TRUE: "ALWAYS_TRUE"
};
var AutomatedReasoningPolicyTestRunResult = {
  FAILED: "FAILED",
  PASSED: "PASSED"
};
var AutomatedReasoningPolicyTestRunStatus = {
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  IN_PROGRESS: "IN_PROGRESS",
  NOT_STARTED: "NOT_STARTED",
  SCHEDULED: "SCHEDULED"
};
var Status = {
  INCOMPATIBLE_ENDPOINT: "INCOMPATIBLE_ENDPOINT",
  REGISTERED: "REGISTERED"
};
var CustomModelDeploymentStatus = {
  ACTIVE: "Active",
  CREATING: "Creating",
  FAILED: "Failed"
};
var CustomModelDeploymentUpdateStatus = {
  UPDATE_COMPLETED: "UpdateCompleted",
  UPDATE_FAILED: "UpdateFailed",
  UPDATING: "Updating"
};
var SortModelsBy = {
  CREATION_TIME: "CreationTime"
};
var SortOrder = {
  ASCENDING: "Ascending",
  DESCENDING: "Descending"
};
var ReasoningEffort = {
  HIGH: "high",
  LOW: "low",
  MEDIUM: "medium"
};
var CustomizationType = {
  CONTINUED_PRE_TRAINING: "CONTINUED_PRE_TRAINING",
  DISTILLATION: "DISTILLATION",
  FINE_TUNING: "FINE_TUNING",
  IMPORTED: "IMPORTED",
  REINFORCEMENT_FINE_TUNING: "REINFORCEMENT_FINE_TUNING"
};
var ModelStatus = {
  ACTIVE: "Active",
  CREATING: "Creating",
  FAILED: "Failed"
};
var EvaluationJobStatus = {
  COMPLETED: "Completed",
  DELETING: "Deleting",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress",
  STOPPED: "Stopped",
  STOPPING: "Stopping"
};
var ApplicationType = {
  MODEL_EVALUATION: "ModelEvaluation",
  RAG_EVALUATION: "RagEvaluation"
};
var EvaluationTaskType = {
  CLASSIFICATION: "Classification",
  CUSTOM: "Custom",
  GENERATION: "Generation",
  QUESTION_AND_ANSWER: "QuestionAndAnswer",
  SUMMARIZATION: "Summarization"
};
var PerformanceConfigLatency = {
  OPTIMIZED: "optimized",
  STANDARD: "standard"
};
var ExternalSourceType = {
  BYTE_CONTENT: "BYTE_CONTENT",
  S3: "S3"
};
var QueryTransformationType = {
  QUERY_DECOMPOSITION: "QUERY_DECOMPOSITION"
};
var AttributeType = {
  BOOLEAN: "BOOLEAN",
  NUMBER: "NUMBER",
  STRING: "STRING",
  STRING_LIST: "STRING_LIST"
};
var SearchType = {
  HYBRID: "HYBRID",
  SEMANTIC: "SEMANTIC"
};
var RerankingMetadataSelectionMode = {
  ALL: "ALL",
  SELECTIVE: "SELECTIVE"
};
var VectorSearchRerankingConfigurationType = {
  BEDROCK_RERANKING_MODEL: "BEDROCK_RERANKING_MODEL"
};
var RetrieveAndGenerateType = {
  EXTERNAL_SOURCES: "EXTERNAL_SOURCES",
  KNOWLEDGE_BASE: "KNOWLEDGE_BASE"
};
var EvaluationJobType = {
  AUTOMATED: "Automated",
  HUMAN: "Human"
};
var SortJobsBy = {
  CREATION_TIME: "CreationTime"
};
var GuardrailContentFilterAction2 = {
  BLOCK: "BLOCK",
  NONE: "NONE"
};
var GuardrailModality2 = {
  IMAGE: "IMAGE",
  TEXT: "TEXT"
};
var GuardrailFilterStrength = {
  HIGH: "HIGH",
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  NONE: "NONE"
};
var GuardrailContentFilterType = {
  HATE: "HATE",
  INSULTS: "INSULTS",
  MISCONDUCT: "MISCONDUCT",
  PROMPT_ATTACK: "PROMPT_ATTACK",
  SEXUAL: "SEXUAL",
  VIOLENCE: "VIOLENCE"
};
var GuardrailContentFiltersTierName2 = {
  CLASSIC: "CLASSIC",
  STANDARD: "STANDARD"
};
var GuardrailContextualGroundingAction2 = {
  BLOCK: "BLOCK",
  NONE: "NONE"
};
var GuardrailContextualGroundingFilterType = {
  GROUNDING: "GROUNDING",
  RELEVANCE: "RELEVANCE"
};
var GuardrailSensitiveInformationAction = {
  ANONYMIZE: "ANONYMIZE",
  BLOCK: "BLOCK",
  NONE: "NONE"
};
var GuardrailPiiEntityType = {
  ADDRESS: "ADDRESS",
  AGE: "AGE",
  AWS_ACCESS_KEY: "AWS_ACCESS_KEY",
  AWS_SECRET_KEY: "AWS_SECRET_KEY",
  CA_HEALTH_NUMBER: "CA_HEALTH_NUMBER",
  CA_SOCIAL_INSURANCE_NUMBER: "CA_SOCIAL_INSURANCE_NUMBER",
  CREDIT_DEBIT_CARD_CVV: "CREDIT_DEBIT_CARD_CVV",
  CREDIT_DEBIT_CARD_EXPIRY: "CREDIT_DEBIT_CARD_EXPIRY",
  CREDIT_DEBIT_CARD_NUMBER: "CREDIT_DEBIT_CARD_NUMBER",
  DRIVER_ID: "DRIVER_ID",
  EMAIL: "EMAIL",
  INTERNATIONAL_BANK_ACCOUNT_NUMBER: "INTERNATIONAL_BANK_ACCOUNT_NUMBER",
  IP_ADDRESS: "IP_ADDRESS",
  LICENSE_PLATE: "LICENSE_PLATE",
  MAC_ADDRESS: "MAC_ADDRESS",
  NAME: "NAME",
  PASSWORD: "PASSWORD",
  PHONE: "PHONE",
  PIN: "PIN",
  SWIFT_CODE: "SWIFT_CODE",
  UK_NATIONAL_HEALTH_SERVICE_NUMBER: "UK_NATIONAL_HEALTH_SERVICE_NUMBER",
  UK_NATIONAL_INSURANCE_NUMBER: "UK_NATIONAL_INSURANCE_NUMBER",
  UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER: "UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER",
  URL: "URL",
  USERNAME: "USERNAME",
  US_BANK_ACCOUNT_NUMBER: "US_BANK_ACCOUNT_NUMBER",
  US_BANK_ROUTING_NUMBER: "US_BANK_ROUTING_NUMBER",
  US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER: "US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER",
  US_PASSPORT_NUMBER: "US_PASSPORT_NUMBER",
  US_SOCIAL_SECURITY_NUMBER: "US_SOCIAL_SECURITY_NUMBER",
  VEHICLE_IDENTIFICATION_NUMBER: "VEHICLE_IDENTIFICATION_NUMBER"
};
var GuardrailTopicsTierName2 = {
  CLASSIC: "CLASSIC",
  STANDARD: "STANDARD"
};
var GuardrailTopicAction2 = {
  BLOCK: "BLOCK",
  NONE: "NONE"
};
var GuardrailTopicType = {
  DENY: "DENY"
};
var GuardrailWordAction2 = {
  BLOCK: "BLOCK",
  NONE: "NONE"
};
var GuardrailManagedWordsType = {
  PROFANITY: "PROFANITY"
};
var GuardrailStatus = {
  CREATING: "CREATING",
  DELETING: "DELETING",
  FAILED: "FAILED",
  READY: "READY",
  UPDATING: "UPDATING",
  VERSIONING: "VERSIONING"
};
var InferenceProfileStatus = {
  ACTIVE: "ACTIVE"
};
var InferenceProfileType = {
  APPLICATION: "APPLICATION",
  SYSTEM_DEFINED: "SYSTEM_DEFINED"
};
var ModelCopyJobStatus = {
  COMPLETED: "Completed",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress"
};
var ModelImportJobStatus = {
  COMPLETED: "Completed",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress"
};
var S3InputFormat = {
  JSONL: "JSONL"
};
var ModelInvocationJobStatus = {
  COMPLETED: "Completed",
  EXPIRED: "Expired",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress",
  PARTIALLY_COMPLETED: "PartiallyCompleted",
  SCHEDULED: "Scheduled",
  STOPPED: "Stopped",
  STOPPING: "Stopping",
  SUBMITTED: "Submitted",
  VALIDATING: "Validating"
};
var ModelCustomization = {
  CONTINUED_PRE_TRAINING: "CONTINUED_PRE_TRAINING",
  DISTILLATION: "DISTILLATION",
  FINE_TUNING: "FINE_TUNING"
};
var InferenceType = {
  ON_DEMAND: "ON_DEMAND",
  PROVISIONED: "PROVISIONED"
};
var ModelModality = {
  EMBEDDING: "EMBEDDING",
  IMAGE: "IMAGE",
  TEXT: "TEXT"
};
var FoundationModelLifecycleStatus = {
  ACTIVE: "ACTIVE",
  LEGACY: "LEGACY"
};
var PromptRouterStatus = {
  AVAILABLE: "AVAILABLE"
};
var PromptRouterType = {
  CUSTOM: "custom",
  DEFAULT: "default"
};
var CommitmentDuration = {
  ONE_MONTH: "OneMonth",
  SIX_MONTHS: "SixMonths"
};
var ProvisionedModelStatus = {
  CREATING: "Creating",
  FAILED: "Failed",
  IN_SERVICE: "InService",
  UPDATING: "Updating"
};
var SortByProvisionedModels = {
  CREATION_TIME: "CreationTime"
};
var AuthorizationStatus = {
  AUTHORIZED: "AUTHORIZED",
  NOT_AUTHORIZED: "NOT_AUTHORIZED"
};
var EntitlementAvailability = {
  AVAILABLE: "AVAILABLE",
  NOT_AVAILABLE: "NOT_AVAILABLE"
};
var RegionAvailability = {
  AVAILABLE: "AVAILABLE",
  NOT_AVAILABLE: "NOT_AVAILABLE"
};
var OfferType = {
  ALL: "ALL",
  PUBLIC: "PUBLIC"
};
var ModelCustomizationJobStatus = {
  COMPLETED: "Completed",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress",
  STOPPED: "Stopped",
  STOPPING: "Stopping"
};
var JobStatusDetails = {
  COMPLETED: "Completed",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress",
  NOT_STARTED: "NotStarted",
  STOPPED: "Stopped",
  STOPPING: "Stopping"
};
var FineTuningJobStatus = {
  COMPLETED: "Completed",
  FAILED: "Failed",
  IN_PROGRESS: "InProgress",
  STOPPED: "Stopped",
  STOPPING: "Stopping"
};
export {
  Command as $Command,
  AccessDeniedException,
  AccessDeniedException$,
  AccountEnforcedGuardrailInferenceInputConfiguration$,
  AccountEnforcedGuardrailOutputConfiguration$,
  AgreementAvailability$,
  AgreementStatus,
  ApplicationType,
  AttributeType,
  AuthorizationStatus,
  AutomatedEvaluationConfig$,
  AutomatedEvaluationCustomMetricConfig$,
  AutomatedEvaluationCustomMetricSource$,
  AutomatedReasoningCheckFinding$,
  AutomatedReasoningCheckImpossibleFinding$,
  AutomatedReasoningCheckInputTextReference$,
  AutomatedReasoningCheckInvalidFinding$,
  AutomatedReasoningCheckLogicWarning$,
  AutomatedReasoningCheckLogicWarningType,
  AutomatedReasoningCheckNoTranslationsFinding$,
  AutomatedReasoningCheckResult,
  AutomatedReasoningCheckRule$,
  AutomatedReasoningCheckSatisfiableFinding$,
  AutomatedReasoningCheckScenario$,
  AutomatedReasoningCheckTooComplexFinding$,
  AutomatedReasoningCheckTranslation$,
  AutomatedReasoningCheckTranslationAmbiguousFinding$,
  AutomatedReasoningCheckTranslationOption$,
  AutomatedReasoningCheckValidFinding$,
  AutomatedReasoningLogicStatement$,
  AutomatedReasoningPolicyAddRuleAnnotation$,
  AutomatedReasoningPolicyAddRuleFromNaturalLanguageAnnotation$,
  AutomatedReasoningPolicyAddRuleMutation$,
  AutomatedReasoningPolicyAddTypeAnnotation$,
  AutomatedReasoningPolicyAddTypeMutation$,
  AutomatedReasoningPolicyAddTypeValue$,
  AutomatedReasoningPolicyAddVariableAnnotation$,
  AutomatedReasoningPolicyAddVariableMutation$,
  AutomatedReasoningPolicyAnnotation$,
  AutomatedReasoningPolicyAnnotationStatus,
  AutomatedReasoningPolicyBuildDocumentContentType,
  AutomatedReasoningPolicyBuildLog$,
  AutomatedReasoningPolicyBuildLogEntry$,
  AutomatedReasoningPolicyBuildMessageType,
  AutomatedReasoningPolicyBuildResultAssetType,
  AutomatedReasoningPolicyBuildResultAssets$,
  AutomatedReasoningPolicyBuildStep$,
  AutomatedReasoningPolicyBuildStepContext$,
  AutomatedReasoningPolicyBuildStepMessage$,
  AutomatedReasoningPolicyBuildWorkflowDocument$,
  AutomatedReasoningPolicyBuildWorkflowRepairContent$,
  AutomatedReasoningPolicyBuildWorkflowSource$,
  AutomatedReasoningPolicyBuildWorkflowStatus,
  AutomatedReasoningPolicyBuildWorkflowSummary$,
  AutomatedReasoningPolicyBuildWorkflowType,
  AutomatedReasoningPolicyDefinition$,
  AutomatedReasoningPolicyDefinitionElement$,
  AutomatedReasoningPolicyDefinitionQualityReport$,
  AutomatedReasoningPolicyDefinitionRule$,
  AutomatedReasoningPolicyDefinitionType$,
  AutomatedReasoningPolicyDefinitionTypeValue$,
  AutomatedReasoningPolicyDefinitionTypeValuePair$,
  AutomatedReasoningPolicyDefinitionVariable$,
  AutomatedReasoningPolicyDeleteRuleAnnotation$,
  AutomatedReasoningPolicyDeleteRuleMutation$,
  AutomatedReasoningPolicyDeleteTypeAnnotation$,
  AutomatedReasoningPolicyDeleteTypeMutation$,
  AutomatedReasoningPolicyDeleteTypeValue$,
  AutomatedReasoningPolicyDeleteVariableAnnotation$,
  AutomatedReasoningPolicyDeleteVariableMutation$,
  AutomatedReasoningPolicyDisjointRuleSet$,
  AutomatedReasoningPolicyGeneratedTestCase$,
  AutomatedReasoningPolicyGeneratedTestCases$,
  AutomatedReasoningPolicyIngestContentAnnotation$,
  AutomatedReasoningPolicyMutation$,
  AutomatedReasoningPolicyPlanning$,
  AutomatedReasoningPolicyScenario$,
  AutomatedReasoningPolicyScenarios$,
  AutomatedReasoningPolicySummary$,
  AutomatedReasoningPolicyTestCase$,
  AutomatedReasoningPolicyTestResult$,
  AutomatedReasoningPolicyTestRunResult,
  AutomatedReasoningPolicyTestRunStatus,
  AutomatedReasoningPolicyTypeValueAnnotation$,
  AutomatedReasoningPolicyUpdateFromRuleFeedbackAnnotation$,
  AutomatedReasoningPolicyUpdateFromScenarioFeedbackAnnotation$,
  AutomatedReasoningPolicyUpdateRuleAnnotation$,
  AutomatedReasoningPolicyUpdateRuleMutation$,
  AutomatedReasoningPolicyUpdateTypeAnnotation$,
  AutomatedReasoningPolicyUpdateTypeMutation$,
  AutomatedReasoningPolicyUpdateTypeValue$,
  AutomatedReasoningPolicyUpdateVariableAnnotation$,
  AutomatedReasoningPolicyUpdateVariableMutation$,
  AutomatedReasoningPolicyWorkflowTypeContent$,
  BatchDeleteEvaluationJob$,
  BatchDeleteEvaluationJobCommand,
  BatchDeleteEvaluationJobError$,
  BatchDeleteEvaluationJobItem$,
  BatchDeleteEvaluationJobRequest$,
  BatchDeleteEvaluationJobResponse$,
  Bedrock,
  BedrockClient,
  BedrockEvaluatorModel$,
  BedrockServiceException,
  BedrockServiceException$,
  ByteContentDoc$,
  CancelAutomatedReasoningPolicyBuildWorkflow$,
  CancelAutomatedReasoningPolicyBuildWorkflowCommand,
  CancelAutomatedReasoningPolicyBuildWorkflowRequest$,
  CancelAutomatedReasoningPolicyBuildWorkflowResponse$,
  CloudWatchConfig$,
  CommitmentDuration,
  ConfigurationOwner,
  ConflictException,
  ConflictException$,
  CreateAutomatedReasoningPolicy$,
  CreateAutomatedReasoningPolicyCommand,
  CreateAutomatedReasoningPolicyRequest$,
  CreateAutomatedReasoningPolicyResponse$,
  CreateAutomatedReasoningPolicyTestCase$,
  CreateAutomatedReasoningPolicyTestCaseCommand,
  CreateAutomatedReasoningPolicyTestCaseRequest$,
  CreateAutomatedReasoningPolicyTestCaseResponse$,
  CreateAutomatedReasoningPolicyVersion$,
  CreateAutomatedReasoningPolicyVersionCommand,
  CreateAutomatedReasoningPolicyVersionRequest$,
  CreateAutomatedReasoningPolicyVersionResponse$,
  CreateCustomModel$,
  CreateCustomModelCommand,
  CreateCustomModelDeployment$,
  CreateCustomModelDeploymentCommand,
  CreateCustomModelDeploymentRequest$,
  CreateCustomModelDeploymentResponse$,
  CreateCustomModelRequest$,
  CreateCustomModelResponse$,
  CreateEvaluationJob$,
  CreateEvaluationJobCommand,
  CreateEvaluationJobRequest$,
  CreateEvaluationJobResponse$,
  CreateFoundationModelAgreement$,
  CreateFoundationModelAgreementCommand,
  CreateFoundationModelAgreementRequest$,
  CreateFoundationModelAgreementResponse$,
  CreateGuardrail$,
  CreateGuardrailCommand,
  CreateGuardrailRequest$,
  CreateGuardrailResponse$,
  CreateGuardrailVersion$,
  CreateGuardrailVersionCommand,
  CreateGuardrailVersionRequest$,
  CreateGuardrailVersionResponse$,
  CreateInferenceProfile$,
  CreateInferenceProfileCommand,
  CreateInferenceProfileRequest$,
  CreateInferenceProfileResponse$,
  CreateMarketplaceModelEndpoint$,
  CreateMarketplaceModelEndpointCommand,
  CreateMarketplaceModelEndpointRequest$,
  CreateMarketplaceModelEndpointResponse$,
  CreateModelCopyJob$,
  CreateModelCopyJobCommand,
  CreateModelCopyJobRequest$,
  CreateModelCopyJobResponse$,
  CreateModelCustomizationJob$,
  CreateModelCustomizationJobCommand,
  CreateModelCustomizationJobRequest$,
  CreateModelCustomizationJobResponse$,
  CreateModelImportJob$,
  CreateModelImportJobCommand,
  CreateModelImportJobRequest$,
  CreateModelImportJobResponse$,
  CreateModelInvocationJob$,
  CreateModelInvocationJobCommand,
  CreateModelInvocationJobRequest$,
  CreateModelInvocationJobResponse$,
  CreatePromptRouter$,
  CreatePromptRouterCommand,
  CreatePromptRouterRequest$,
  CreatePromptRouterResponse$,
  CreateProvisionedModelThroughput$,
  CreateProvisionedModelThroughputCommand,
  CreateProvisionedModelThroughputRequest$,
  CreateProvisionedModelThroughputResponse$,
  CustomMetricBedrockEvaluatorModel$,
  CustomMetricDefinition$,
  CustomMetricEvaluatorModelConfig$,
  CustomModelDeploymentStatus,
  CustomModelDeploymentSummary$,
  CustomModelDeploymentUpdateDetails$,
  CustomModelDeploymentUpdateStatus,
  CustomModelSummary$,
  CustomModelUnits$,
  CustomizationConfig$,
  CustomizationType,
  DataProcessingDetails$,
  DeleteAutomatedReasoningPolicy$,
  DeleteAutomatedReasoningPolicyBuildWorkflow$,
  DeleteAutomatedReasoningPolicyBuildWorkflowCommand,
  DeleteAutomatedReasoningPolicyBuildWorkflowRequest$,
  DeleteAutomatedReasoningPolicyBuildWorkflowResponse$,
  DeleteAutomatedReasoningPolicyCommand,
  DeleteAutomatedReasoningPolicyRequest$,
  DeleteAutomatedReasoningPolicyResponse$,
  DeleteAutomatedReasoningPolicyTestCase$,
  DeleteAutomatedReasoningPolicyTestCaseCommand,
  DeleteAutomatedReasoningPolicyTestCaseRequest$,
  DeleteAutomatedReasoningPolicyTestCaseResponse$,
  DeleteCustomModel$,
  DeleteCustomModelCommand,
  DeleteCustomModelDeployment$,
  DeleteCustomModelDeploymentCommand,
  DeleteCustomModelDeploymentRequest$,
  DeleteCustomModelDeploymentResponse$,
  DeleteCustomModelRequest$,
  DeleteCustomModelResponse$,
  DeleteEnforcedGuardrailConfiguration$,
  DeleteEnforcedGuardrailConfigurationCommand,
  DeleteEnforcedGuardrailConfigurationRequest$,
  DeleteEnforcedGuardrailConfigurationResponse$,
  DeleteFoundationModelAgreement$,
  DeleteFoundationModelAgreementCommand,
  DeleteFoundationModelAgreementRequest$,
  DeleteFoundationModelAgreementResponse$,
  DeleteGuardrail$,
  DeleteGuardrailCommand,
  DeleteGuardrailRequest$,
  DeleteGuardrailResponse$,
  DeleteImportedModel$,
  DeleteImportedModelCommand,
  DeleteImportedModelRequest$,
  DeleteImportedModelResponse$,
  DeleteInferenceProfile$,
  DeleteInferenceProfileCommand,
  DeleteInferenceProfileRequest$,
  DeleteInferenceProfileResponse$,
  DeleteMarketplaceModelEndpoint$,
  DeleteMarketplaceModelEndpointCommand,
  DeleteMarketplaceModelEndpointRequest$,
  DeleteMarketplaceModelEndpointResponse$,
  DeleteModelInvocationLoggingConfiguration$,
  DeleteModelInvocationLoggingConfigurationCommand,
  DeleteModelInvocationLoggingConfigurationRequest$,
  DeleteModelInvocationLoggingConfigurationResponse$,
  DeletePromptRouter$,
  DeletePromptRouterCommand,
  DeletePromptRouterRequest$,
  DeletePromptRouterResponse$,
  DeleteProvisionedModelThroughput$,
  DeleteProvisionedModelThroughputCommand,
  DeleteProvisionedModelThroughputRequest$,
  DeleteProvisionedModelThroughputResponse$,
  DeregisterMarketplaceModelEndpoint$,
  DeregisterMarketplaceModelEndpointCommand,
  DeregisterMarketplaceModelEndpointRequest$,
  DeregisterMarketplaceModelEndpointResponse$,
  DimensionalPriceRate$,
  DistillationConfig$,
  EndpointConfig$,
  EntitlementAvailability,
  EvaluationBedrockModel$,
  EvaluationConfig$,
  EvaluationDataset$,
  EvaluationDatasetLocation$,
  EvaluationDatasetMetricConfig$,
  EvaluationInferenceConfig$,
  EvaluationInferenceConfigSummary$,
  EvaluationJobStatus,
  EvaluationJobType,
  EvaluationModelConfig$,
  EvaluationModelConfigSummary$,
  EvaluationOutputDataConfig$,
  EvaluationPrecomputedInferenceSource$,
  EvaluationPrecomputedRagSourceConfig$,
  EvaluationPrecomputedRetrieveAndGenerateSourceConfig$,
  EvaluationPrecomputedRetrieveSourceConfig$,
  EvaluationRagConfigSummary$,
  EvaluationSummary$,
  EvaluationTaskType,
  EvaluatorModelConfig$,
  ExportAutomatedReasoningPolicyVersion$,
  ExportAutomatedReasoningPolicyVersionCommand,
  ExportAutomatedReasoningPolicyVersionRequest$,
  ExportAutomatedReasoningPolicyVersionResponse$,
  ExternalSource$,
  ExternalSourceType,
  ExternalSourcesGenerationConfiguration$,
  ExternalSourcesRetrieveAndGenerateConfiguration$,
  FieldForReranking$,
  FilterAttribute$,
  FineTuningJobStatus,
  FoundationModelDetails$,
  FoundationModelLifecycle$,
  FoundationModelLifecycleStatus,
  FoundationModelSummary$,
  GenerationConfiguration$,
  GetAutomatedReasoningPolicy$,
  GetAutomatedReasoningPolicyAnnotations$,
  GetAutomatedReasoningPolicyAnnotationsCommand,
  GetAutomatedReasoningPolicyAnnotationsRequest$,
  GetAutomatedReasoningPolicyAnnotationsResponse$,
  GetAutomatedReasoningPolicyBuildWorkflow$,
  GetAutomatedReasoningPolicyBuildWorkflowCommand,
  GetAutomatedReasoningPolicyBuildWorkflowRequest$,
  GetAutomatedReasoningPolicyBuildWorkflowResponse$,
  GetAutomatedReasoningPolicyBuildWorkflowResultAssets$,
  GetAutomatedReasoningPolicyBuildWorkflowResultAssetsCommand,
  GetAutomatedReasoningPolicyBuildWorkflowResultAssetsRequest$,
  GetAutomatedReasoningPolicyBuildWorkflowResultAssetsResponse$,
  GetAutomatedReasoningPolicyCommand,
  GetAutomatedReasoningPolicyNextScenario$,
  GetAutomatedReasoningPolicyNextScenarioCommand,
  GetAutomatedReasoningPolicyNextScenarioRequest$,
  GetAutomatedReasoningPolicyNextScenarioResponse$,
  GetAutomatedReasoningPolicyRequest$,
  GetAutomatedReasoningPolicyResponse$,
  GetAutomatedReasoningPolicyTestCase$,
  GetAutomatedReasoningPolicyTestCaseCommand,
  GetAutomatedReasoningPolicyTestCaseRequest$,
  GetAutomatedReasoningPolicyTestCaseResponse$,
  GetAutomatedReasoningPolicyTestResult$,
  GetAutomatedReasoningPolicyTestResultCommand,
  GetAutomatedReasoningPolicyTestResultRequest$,
  GetAutomatedReasoningPolicyTestResultResponse$,
  GetCustomModel$,
  GetCustomModelCommand,
  GetCustomModelDeployment$,
  GetCustomModelDeploymentCommand,
  GetCustomModelDeploymentRequest$,
  GetCustomModelDeploymentResponse$,
  GetCustomModelRequest$,
  GetCustomModelResponse$,
  GetEvaluationJob$,
  GetEvaluationJobCommand,
  GetEvaluationJobRequest$,
  GetEvaluationJobResponse$,
  GetFoundationModel$,
  GetFoundationModelAvailability$,
  GetFoundationModelAvailabilityCommand,
  GetFoundationModelAvailabilityRequest$,
  GetFoundationModelAvailabilityResponse$,
  GetFoundationModelCommand,
  GetFoundationModelRequest$,
  GetFoundationModelResponse$,
  GetGuardrail$,
  GetGuardrailCommand,
  GetGuardrailRequest$,
  GetGuardrailResponse$,
  GetImportedModel$,
  GetImportedModelCommand,
  GetImportedModelRequest$,
  GetImportedModelResponse$,
  GetInferenceProfile$,
  GetInferenceProfileCommand,
  GetInferenceProfileRequest$,
  GetInferenceProfileResponse$,
  GetMarketplaceModelEndpoint$,
  GetMarketplaceModelEndpointCommand,
  GetMarketplaceModelEndpointRequest$,
  GetMarketplaceModelEndpointResponse$,
  GetModelCopyJob$,
  GetModelCopyJobCommand,
  GetModelCopyJobRequest$,
  GetModelCopyJobResponse$,
  GetModelCustomizationJob$,
  GetModelCustomizationJobCommand,
  GetModelCustomizationJobRequest$,
  GetModelCustomizationJobResponse$,
  GetModelImportJob$,
  GetModelImportJobCommand,
  GetModelImportJobRequest$,
  GetModelImportJobResponse$,
  GetModelInvocationJob$,
  GetModelInvocationJobCommand,
  GetModelInvocationJobRequest$,
  GetModelInvocationJobResponse$,
  GetModelInvocationLoggingConfiguration$,
  GetModelInvocationLoggingConfigurationCommand,
  GetModelInvocationLoggingConfigurationRequest$,
  GetModelInvocationLoggingConfigurationResponse$,
  GetPromptRouter$,
  GetPromptRouterCommand,
  GetPromptRouterRequest$,
  GetPromptRouterResponse$,
  GetProvisionedModelThroughput$,
  GetProvisionedModelThroughputCommand,
  GetProvisionedModelThroughputRequest$,
  GetProvisionedModelThroughputResponse$,
  GetUseCaseForModelAccess$,
  GetUseCaseForModelAccessCommand,
  GetUseCaseForModelAccessRequest$,
  GetUseCaseForModelAccessResponse$,
  GraderConfig$,
  GuardrailAutomatedReasoningPolicy$,
  GuardrailAutomatedReasoningPolicyConfig$,
  GuardrailConfiguration$,
  GuardrailContentFilter$,
  GuardrailContentFilterAction2 as GuardrailContentFilterAction,
  GuardrailContentFilterConfig$,
  GuardrailContentFilterType,
  GuardrailContentFiltersTier$,
  GuardrailContentFiltersTierConfig$,
  GuardrailContentFiltersTierName2 as GuardrailContentFiltersTierName,
  GuardrailContentPolicy$,
  GuardrailContentPolicyConfig$,
  GuardrailContextualGroundingAction2 as GuardrailContextualGroundingAction,
  GuardrailContextualGroundingFilter$,
  GuardrailContextualGroundingFilterConfig$,
  GuardrailContextualGroundingFilterType,
  GuardrailContextualGroundingPolicy$,
  GuardrailContextualGroundingPolicyConfig$,
  GuardrailCrossRegionConfig$,
  GuardrailCrossRegionDetails$,
  GuardrailFilterStrength,
  GuardrailManagedWords$,
  GuardrailManagedWordsConfig$,
  GuardrailManagedWordsType,
  GuardrailModality2 as GuardrailModality,
  GuardrailPiiEntity$,
  GuardrailPiiEntityConfig$,
  GuardrailPiiEntityType,
  GuardrailRegex$,
  GuardrailRegexConfig$,
  GuardrailSensitiveInformationAction,
  GuardrailSensitiveInformationPolicy$,
  GuardrailSensitiveInformationPolicyConfig$,
  GuardrailStatus,
  GuardrailSummary$,
  GuardrailTopic$,
  GuardrailTopicAction2 as GuardrailTopicAction,
  GuardrailTopicConfig$,
  GuardrailTopicPolicy$,
  GuardrailTopicPolicyConfig$,
  GuardrailTopicType,
  GuardrailTopicsTier$,
  GuardrailTopicsTierConfig$,
  GuardrailTopicsTierName2 as GuardrailTopicsTierName,
  GuardrailWord$,
  GuardrailWordAction2 as GuardrailWordAction,
  GuardrailWordConfig$,
  GuardrailWordPolicy$,
  GuardrailWordPolicyConfig$,
  HumanEvaluationConfig$,
  HumanEvaluationCustomMetric$,
  HumanWorkflowConfig$,
  ImplicitFilterConfiguration$,
  ImportedModelSummary$,
  InferenceProfileModel$,
  InferenceProfileModelSource$,
  InferenceProfileStatus,
  InferenceProfileSummary$,
  InferenceProfileType,
  InferenceType,
  InputTags,
  InternalServerException,
  InternalServerException$,
  InvocationLogSource$,
  InvocationLogsConfig$,
  JobStatusDetails,
  KbInferenceConfig$,
  KnowledgeBaseConfig$,
  KnowledgeBaseRetrievalConfiguration$,
  KnowledgeBaseRetrieveAndGenerateConfiguration$,
  KnowledgeBaseVectorSearchConfiguration$,
  LambdaGraderConfig$,
  LegalTerm$,
  ListAutomatedReasoningPolicies$,
  ListAutomatedReasoningPoliciesCommand,
  ListAutomatedReasoningPoliciesRequest$,
  ListAutomatedReasoningPoliciesResponse$,
  ListAutomatedReasoningPolicyBuildWorkflows$,
  ListAutomatedReasoningPolicyBuildWorkflowsCommand,
  ListAutomatedReasoningPolicyBuildWorkflowsRequest$,
  ListAutomatedReasoningPolicyBuildWorkflowsResponse$,
  ListAutomatedReasoningPolicyTestCases$,
  ListAutomatedReasoningPolicyTestCasesCommand,
  ListAutomatedReasoningPolicyTestCasesRequest$,
  ListAutomatedReasoningPolicyTestCasesResponse$,
  ListAutomatedReasoningPolicyTestResults$,
  ListAutomatedReasoningPolicyTestResultsCommand,
  ListAutomatedReasoningPolicyTestResultsRequest$,
  ListAutomatedReasoningPolicyTestResultsResponse$,
  ListCustomModelDeployments$,
  ListCustomModelDeploymentsCommand,
  ListCustomModelDeploymentsRequest$,
  ListCustomModelDeploymentsResponse$,
  ListCustomModels$,
  ListCustomModelsCommand,
  ListCustomModelsRequest$,
  ListCustomModelsResponse$,
  ListEnforcedGuardrailsConfiguration$,
  ListEnforcedGuardrailsConfigurationCommand,
  ListEnforcedGuardrailsConfigurationRequest$,
  ListEnforcedGuardrailsConfigurationResponse$,
  ListEvaluationJobs$,
  ListEvaluationJobsCommand,
  ListEvaluationJobsRequest$,
  ListEvaluationJobsResponse$,
  ListFoundationModelAgreementOffers$,
  ListFoundationModelAgreementOffersCommand,
  ListFoundationModelAgreementOffersRequest$,
  ListFoundationModelAgreementOffersResponse$,
  ListFoundationModels$,
  ListFoundationModelsCommand,
  ListFoundationModelsRequest$,
  ListFoundationModelsResponse$,
  ListGuardrails$,
  ListGuardrailsCommand,
  ListGuardrailsRequest$,
  ListGuardrailsResponse$,
  ListImportedModels$,
  ListImportedModelsCommand,
  ListImportedModelsRequest$,
  ListImportedModelsResponse$,
  ListInferenceProfiles$,
  ListInferenceProfilesCommand,
  ListInferenceProfilesRequest$,
  ListInferenceProfilesResponse$,
  ListMarketplaceModelEndpoints$,
  ListMarketplaceModelEndpointsCommand,
  ListMarketplaceModelEndpointsRequest$,
  ListMarketplaceModelEndpointsResponse$,
  ListModelCopyJobs$,
  ListModelCopyJobsCommand,
  ListModelCopyJobsRequest$,
  ListModelCopyJobsResponse$,
  ListModelCustomizationJobs$,
  ListModelCustomizationJobsCommand,
  ListModelCustomizationJobsRequest$,
  ListModelCustomizationJobsResponse$,
  ListModelImportJobs$,
  ListModelImportJobsCommand,
  ListModelImportJobsRequest$,
  ListModelImportJobsResponse$,
  ListModelInvocationJobs$,
  ListModelInvocationJobsCommand,
  ListModelInvocationJobsRequest$,
  ListModelInvocationJobsResponse$,
  ListPromptRouters$,
  ListPromptRoutersCommand,
  ListPromptRoutersRequest$,
  ListPromptRoutersResponse$,
  ListProvisionedModelThroughputs$,
  ListProvisionedModelThroughputsCommand,
  ListProvisionedModelThroughputsRequest$,
  ListProvisionedModelThroughputsResponse$,
  ListTagsForResource$,
  ListTagsForResourceCommand,
  ListTagsForResourceRequest$,
  ListTagsForResourceResponse$,
  LoggingConfig$,
  MarketplaceModelEndpoint$,
  MarketplaceModelEndpointSummary$,
  MetadataAttributeSchema$,
  MetadataConfigurationForReranking$,
  ModelCopyJobStatus,
  ModelCopyJobSummary$,
  ModelCustomization,
  ModelCustomizationJobStatus,
  ModelCustomizationJobSummary$,
  ModelDataSource$,
  ModelImportJobStatus,
  ModelImportJobSummary$,
  ModelInvocationJobInputDataConfig$,
  ModelInvocationJobOutputDataConfig$,
  ModelInvocationJobS3InputDataConfig$,
  ModelInvocationJobS3OutputDataConfig$,
  ModelInvocationJobStatus,
  ModelInvocationJobSummary$,
  ModelModality,
  ModelStatus,
  Offer$,
  OfferType,
  OrchestrationConfiguration$,
  OutputDataConfig$,
  PerformanceConfigLatency,
  PerformanceConfiguration$,
  PricingTerm$,
  PromptRouterStatus,
  PromptRouterSummary$,
  PromptRouterTargetModel$,
  PromptRouterType,
  PromptTemplate$,
  ProvisionedModelStatus,
  ProvisionedModelSummary$,
  PutEnforcedGuardrailConfiguration$,
  PutEnforcedGuardrailConfigurationCommand,
  PutEnforcedGuardrailConfigurationRequest$,
  PutEnforcedGuardrailConfigurationResponse$,
  PutModelInvocationLoggingConfiguration$,
  PutModelInvocationLoggingConfigurationCommand,
  PutModelInvocationLoggingConfigurationRequest$,
  PutModelInvocationLoggingConfigurationResponse$,
  PutUseCaseForModelAccess$,
  PutUseCaseForModelAccessCommand,
  PutUseCaseForModelAccessRequest$,
  PutUseCaseForModelAccessResponse$,
  QueryTransformationConfiguration$,
  QueryTransformationType,
  RAGConfig$,
  RFTConfig$,
  RFTHyperParameters$,
  RatingScaleItem$,
  RatingScaleItemValue$,
  ReasoningEffort,
  RegionAvailability,
  RegisterMarketplaceModelEndpoint$,
  RegisterMarketplaceModelEndpointCommand,
  RegisterMarketplaceModelEndpointRequest$,
  RegisterMarketplaceModelEndpointResponse$,
  RequestMetadataBaseFilters$,
  RequestMetadataFilters$,
  RerankingMetadataSelectionMode,
  RerankingMetadataSelectiveModeConfiguration$,
  ResourceInUseException,
  ResourceInUseException$,
  ResourceNotFoundException,
  ResourceNotFoundException$,
  RetrievalFilter$,
  RetrieveAndGenerateConfiguration$,
  RetrieveAndGenerateType,
  RetrieveConfig$,
  RoutingCriteria$,
  S3Config$,
  S3DataSource$,
  S3InputFormat,
  S3ObjectDoc$,
  SageMakerEndpoint$,
  SearchType,
  ServiceQuotaExceededException,
  ServiceQuotaExceededException$,
  ServiceUnavailableException,
  ServiceUnavailableException$,
  SortByProvisionedModels,
  SortJobsBy,
  SortModelsBy,
  SortOrder,
  StartAutomatedReasoningPolicyBuildWorkflow$,
  StartAutomatedReasoningPolicyBuildWorkflowCommand,
  StartAutomatedReasoningPolicyBuildWorkflowRequest$,
  StartAutomatedReasoningPolicyBuildWorkflowResponse$,
  StartAutomatedReasoningPolicyTestWorkflow$,
  StartAutomatedReasoningPolicyTestWorkflowCommand,
  StartAutomatedReasoningPolicyTestWorkflowRequest$,
  StartAutomatedReasoningPolicyTestWorkflowResponse$,
  Status,
  StatusDetails$,
  StopEvaluationJob$,
  StopEvaluationJobCommand,
  StopEvaluationJobRequest$,
  StopEvaluationJobResponse$,
  StopModelCustomizationJob$,
  StopModelCustomizationJobCommand,
  StopModelCustomizationJobRequest$,
  StopModelCustomizationJobResponse$,
  StopModelInvocationJob$,
  StopModelInvocationJobCommand,
  StopModelInvocationJobRequest$,
  StopModelInvocationJobResponse$,
  SupportTerm$,
  Tag$,
  TagResource$,
  TagResourceCommand,
  TagResourceRequest$,
  TagResourceResponse$,
  TeacherModelConfig$,
  TermDetails$,
  TextInferenceConfig$,
  ThrottlingException,
  ThrottlingException$,
  TooManyTagsException,
  TooManyTagsException$,
  TrainingDataConfig$,
  TrainingDetails$,
  TrainingMetrics$,
  UntagResource$,
  UntagResourceCommand,
  UntagResourceRequest$,
  UntagResourceResponse$,
  UpdateAutomatedReasoningPolicy$,
  UpdateAutomatedReasoningPolicyAnnotations$,
  UpdateAutomatedReasoningPolicyAnnotationsCommand,
  UpdateAutomatedReasoningPolicyAnnotationsRequest$,
  UpdateAutomatedReasoningPolicyAnnotationsResponse$,
  UpdateAutomatedReasoningPolicyCommand,
  UpdateAutomatedReasoningPolicyRequest$,
  UpdateAutomatedReasoningPolicyResponse$,
  UpdateAutomatedReasoningPolicyTestCase$,
  UpdateAutomatedReasoningPolicyTestCaseCommand,
  UpdateAutomatedReasoningPolicyTestCaseRequest$,
  UpdateAutomatedReasoningPolicyTestCaseResponse$,
  UpdateCustomModelDeployment$,
  UpdateCustomModelDeploymentCommand,
  UpdateCustomModelDeploymentRequest$,
  UpdateCustomModelDeploymentResponse$,
  UpdateGuardrail$,
  UpdateGuardrailCommand,
  UpdateGuardrailRequest$,
  UpdateGuardrailResponse$,
  UpdateMarketplaceModelEndpoint$,
  UpdateMarketplaceModelEndpointCommand,
  UpdateMarketplaceModelEndpointRequest$,
  UpdateMarketplaceModelEndpointResponse$,
  UpdateProvisionedModelThroughput$,
  UpdateProvisionedModelThroughputCommand,
  UpdateProvisionedModelThroughputRequest$,
  UpdateProvisionedModelThroughputResponse$,
  ValidationDataConfig$,
  ValidationDetails$,
  ValidationException,
  ValidationException$,
  Validator$,
  ValidatorMetric$,
  ValidityTerm$,
  VectorSearchBedrockRerankingConfiguration$,
  VectorSearchBedrockRerankingModelConfiguration$,
  VectorSearchRerankingConfiguration$,
  VectorSearchRerankingConfigurationType,
  VpcConfig$,
  Client as __Client,
  paginateListAutomatedReasoningPolicies,
  paginateListAutomatedReasoningPolicyBuildWorkflows,
  paginateListAutomatedReasoningPolicyTestCases,
  paginateListAutomatedReasoningPolicyTestResults,
  paginateListCustomModelDeployments,
  paginateListCustomModels,
  paginateListEnforcedGuardrailsConfiguration,
  paginateListEvaluationJobs,
  paginateListGuardrails,
  paginateListImportedModels,
  paginateListInferenceProfiles,
  paginateListMarketplaceModelEndpoints,
  paginateListModelCopyJobs,
  paginateListModelCustomizationJobs,
  paginateListModelImportJobs,
  paginateListModelInvocationJobs,
  paginateListPromptRouters,
  paginateListProvisionedModelThroughputs
};
