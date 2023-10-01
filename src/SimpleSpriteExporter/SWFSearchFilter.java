package SimpleSpriteExporter;

enum SWFFilterParam
{
  contains,
  endsWith,
  startsWith;
}

public class SWFSearchFilter {
    SWFFilterParam type;
    String paramString;

    enum SWFFilterParam {
        contains,
        endsWith,
        startsWith;
    }

    public boolean checkSWFExtractParam(String nameToCheck, boolean ignoreCaps) {
        if (this.type == SWFFilterParam.contains) {
            if (ignoreCaps) {
                return nameToCheck.toLowerCase().contains(this.paramString.toLowerCase());
            }
            return nameToCheck.contains(this.paramString);
        }
        if (this.type == SWFFilterParam.endsWith) {
            if (ignoreCaps) {
                return nameToCheck.toLowerCase().endsWith(this.paramString.toLowerCase());
            }
            return nameToCheck.endsWith(this.paramString);
        }

        if (ignoreCaps) {
            return nameToCheck.toLowerCase().startsWith(this.paramString.toLowerCase());
        }
        return nameToCheck.startsWith(this.paramString);
    }
}
