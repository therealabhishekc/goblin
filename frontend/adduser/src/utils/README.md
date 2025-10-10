# Utility Functions

## Date Formatter (`dateFormatter.js`)

Utility functions for formatting dates and times to CST (Central Standard Time) / CDT (Central Daylight Time) timezone.

### Why CST?

All timestamps in the database are stored in UTC. The date formatter converts these UTC timestamps to the Central timezone (America/Chicago) which automatically handles:
- **CST** (Central Standard Time): UTC-6 (November - March)
- **CDT** (Central Daylight Time): UTC-5 (March - November)

### Available Functions

#### 1. `formatToCST(dateString, options)`

Main formatting function with full control over display format.

**Parameters:**
- `dateString` (string|Date): ISO date string or Date object
- `options` (object, optional): Custom formatting options

**Returns:** Formatted date string with timezone abbreviation (CST/CDT)

**Example:**
```javascript
import { formatToCST } from '../utils/dateFormatter';

// Input: "2024-10-10T03:33:39Z" (UTC)
formatToCST("2024-10-10T03:33:39Z");
// Output: "10/09/2024, 10:33:39 PM CDT"

// Custom options
formatToCST("2024-10-10T03:33:39Z", {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});
// Output: "October 9, 2024, 10:33:39 PM CDT"
```

---

#### 2. `formatDateOnlyCST(dateString)`

Format date without time component.

**Returns:** Date only (MM/DD/YYYY)

**Example:**
```javascript
import { formatDateOnlyCST } from '../utils/dateFormatter';

formatDateOnlyCST("2024-10-10T03:33:39Z");
// Output: "10/09/2024"
```

---

#### 3. `formatDateTimeCST(dateString)`

Format date and time without timezone abbreviation.

**Returns:** Date and time (MM/DD/YYYY, HH:MM:SS AM/PM)

**Example:**
```javascript
import { formatDateTimeCST } from '../utils/dateFormatter';

formatDateTimeCST("2024-10-10T03:33:39Z");
// Output: "10/09/2024, 10:33:39 PM"
```

---

#### 4. `formatDateCompactCST(dateString)`

Format date in compact format (shorter, no leading zeros).

**Returns:** Compact date and time (M/D/YYYY h:MM AM/PM)

**Example:**
```javascript
import { formatDateCompactCST } from '../utils/dateFormatter';

formatDateCompactCST("2024-10-10T03:33:39Z");
// Output: "10/9/2024 10:33 PM"
```

---

#### 5. `getRelativeTime(dateString)`

Get relative time description (e.g., "2 hours ago").

**Returns:** Human-readable relative time string

**Example:**
```javascript
import { getRelativeTime } from '../utils/dateFormatter';

getRelativeTime("2024-10-09T22:33:39Z"); // 2 hours ago
// Output: "2 hours ago"

getRelativeTime("2024-10-08T22:33:39Z"); // yesterday
// Output: "1 day ago"

getRelativeTime("2024-09-09T22:33:39Z"); // last month
// Output: "1 month ago"
```

---

## Usage in Components

### Import the utility:

```javascript
import { formatToCST } from '../utils/dateFormatter';
// OR import multiple functions
import { formatToCST, formatDateOnlyCST, getRelativeTime } from '../utils/dateFormatter';
```

### Use in JSX:

```javascript
function UserComponent({ user }) {
  return (
    <div>
      <p>Created: {formatToCST(user.created_at)}</p>
      <p>Last Active: {getRelativeTime(user.last_interaction)}</p>
      <p>Join Date: {formatDateOnlyCST(user.created_at)}</p>
    </div>
  );
}
```

---

## Timezone Conversion Examples

### UTC to CST Conversion:

| UTC Time | CST Time | CDT Time |
|----------|----------|----------|
| 03:33:39 AM | 09:33:39 PM (previous day) | 10:33:39 PM (previous day) |
| 12:00:00 PM | 06:00:00 AM | 07:00:00 AM |
| 06:00:00 PM | 12:00:00 PM | 01:00:00 PM |
| 11:59:59 PM | 05:59:59 PM | 06:59:59 PM |

**Note:** CST is UTC-6, CDT is UTC-5. The function automatically handles DST transitions.

---

## Error Handling

All functions include error handling and return safe default values:

- **Invalid date:** Returns `"Invalid Date"`
- **Null/undefined:** Returns `"N/A"`
- **Format error:** Logs error to console and returns fallback

**Example:**
```javascript
formatToCST(null);        // Returns: "N/A"
formatToCST(undefined);   // Returns: "N/A"
formatToCST("invalid");   // Returns: "Invalid Date"
```

---

## Where It's Used

Currently implemented in:
- ✅ **UpdateUserForm.js** - Created date, Last interaction
- ✅ All user information displays
- ✅ Date fields in user cards

To add to other components:
1. Import the utility
2. Replace `new Date().toLocaleString()` with `formatToCST()`
3. Choose the appropriate format function

---

## Testing

### Test in Browser Console:

```javascript
// Test UTC to CST conversion
const testDate = "2024-10-10T03:33:39Z";

// Test each function
console.log("Full:", formatToCST(testDate));
console.log("Date Only:", formatDateOnlyCST(testDate));
console.log("DateTime:", formatDateTimeCST(testDate));
console.log("Compact:", formatDateCompactCST(testDate));
console.log("Relative:", getRelativeTime(testDate));
```

### Expected Output:
```
Full: 10/09/2024, 10:33:39 PM CDT
Date Only: 10/09/2024
DateTime: 10/09/2024, 10:33:39 PM
Compact: 10/9/2024 10:33 PM
Relative: 5 hours ago (varies based on current time)
```

---

## Customization

### Change Timezone:

To use a different timezone, modify the `timeZone` option:

```javascript
// EST/EDT
const options = { timeZone: 'America/New_York' };

// PST/PDT
const options = { timeZone: 'America/Los_Angeles' };

// MST/MDT
const options = { timeZone: 'America/Denver' };
```

### Change Date Format:

```javascript
// European format (DD/MM/YYYY)
formatToCST(date, {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric'
});

// Long format
formatToCST(date, {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
});
// Output: "Wednesday, October 9, 2024, 10:33:39 PM CDT"
```

---

## Best Practices

1. **Always use the utility for timestamps** - Don't use `new Date().toLocaleString()` directly
2. **Choose the right function** - Use `formatDateOnlyCST` for dates without time
3. **Consider relative time** - Use `getRelativeTime()` for recent events
4. **Handle null values** - The utility handles it, but validate your data
5. **Be consistent** - Use the same format throughout your app

---

## Additional Resources

- [Intl.DateTimeFormat - MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat)
- [IANA Timezone Database](https://www.iana.org/time-zones)
- [Date and Time in JavaScript](https://javascript.info/date)

---

## Maintenance

**Last Updated:** October 9, 2024  
**Author:** System  
**Version:** 1.0.0
