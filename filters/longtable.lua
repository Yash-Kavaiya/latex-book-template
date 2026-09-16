-- Give LaTeX tables page breaks, repeated headings and safe width constraints.
-- Pandoc's native longtable writer retains captions/labels and repeats TableHead.
function Table(table)
  if FORMAT ~= "latex" then return nil end
  local columns = #table.colspecs
  if columns == 0 then return nil end

  -- Explicit widths are normalized to the available line width.  Automatic
  -- widths remain automatic; the template's longtable setup then constrains
  -- their padding. This avoids guessing from byte lengths or injecting TeX.
  local total = 0
  for _, spec in ipairs(table.colspecs) do
    local width = spec[2]
    if width and width > 0 then total = total + width end
  end
  if total > 1 then
    for i, spec in ipairs(table.colspecs) do
      if spec[2] and spec[2] > 0 then table.colspecs[i][2] = spec[2] / total end
    end
  end
  if columns >= 6 then
    -- Keep longtable (and therefore page breaks) rather than resizebox.  A
    -- local smaller font is readable and lets p{} columns wrap naturally.
    return {
      pandoc.RawBlock("latex", "\\begingroup\\small\\setlength{\\tabcolsep}{2pt}"),
      table,
      pandoc.RawBlock("latex", "\\endgroup")
    }
  end
  return table
end

function Div(div)
  if FORMAT == "latex" and div.classes:includes("landscape") then
    return {
      pandoc.RawBlock("latex", "\\begin{landscape}"),
      table.unpack(div.content),
      pandoc.RawBlock("latex", "\\end{landscape}")
    }
  end
end
