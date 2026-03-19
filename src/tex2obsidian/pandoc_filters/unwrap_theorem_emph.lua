-- unwrap_theorem_emph.lua
-- Pandoc Lua filter: strips italic wrapping from plain-style theorem bodies.
--
-- Problem: \theoremstyle{plain} (theorem, corollary, lemma, proposition)
-- makes LaTeX render the body in italic. Pandoc reproduces this by wrapping
-- the body in Emph, which creates stray * around math in markdown output.
--
-- Heuristic: an Emph node inside a plain-style Div is a pandoc wrapper
-- (not author-intentional) if it contains Math nodes OR more than 5 Str tokens.

local plain_styles = {
  theorem = true,
  corollary = true,
  lemma = true,
  proposition = true,
}

local function scan_inlines(inlines)
  local has_math = false
  local str_count = 0
  for _, el in ipairs(inlines) do
    if el.t == "Math" then
      has_math = true
    elseif el.t == "Str" then
      str_count = str_count + 1
    elseif el.content then
      local sub_math, sub_count = scan_inlines(el.content)
      has_math = has_math or sub_math
      str_count = str_count + sub_count
    end
  end
  return has_math, str_count
end

function Div(el)
  local dominated = false
  for _, cls in ipairs(el.classes) do
    if plain_styles[cls] then
      dominated = true
      break
    end
  end
  if not dominated then return end

  return el:walk {
    Emph = function(emph)
      local has_math, str_count = scan_inlines(emph.content)
      if has_math or str_count > 5 then
        return emph.content
      end
    end
  }
end
