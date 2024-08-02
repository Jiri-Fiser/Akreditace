<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:ak="http://ki.ujep.cz/ns/akreditace"
                xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xslt="http://www.w3.org/1999/XSL/Transform"
                xmlns:xt="http:/ki.ujep.cz/ns/xtools"
                xmlns:f="http://ki.ujep.cz/ns/functions"
                exclude-result-prefixes="ak">

    <!-- Definování výstupního formátu -->
    <xsl:output method="xml" indent="yes" doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
                doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"/>

    <xsl:template match="xt:contents">
            <div class="annotation"><xsl:value-of select="@xpath"/></div>
            <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="xt:string">
        <span class="annotation"><xsl:value-of select="@xpath"/></span>
        <xsl:apply-templates/>
    </xsl:template>

    <!-- Šablona pro kořenový element -->
    <xsl:template match="ak:project">
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <title>Transformovaný dokument</title>
            </head>
            <body>
                <xsl:apply-templates/>
                <link rel="stylesheet" type="text/css" href="akreditace.css"/>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="ak:studijní_programy">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="ak:studijní_program">
        <div class="program">
            <xslt:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="ak:A-I">
        <div class="section" head="A-I – Základní informace o žádosti o akreditaci">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="ak:název-vysoké-školy">
        <div class="bh">Název vysoké školy:</div>
        <div class="bv"><xsl:apply-templates/></div>
    </xsl:template>

    <xsl:template match="ak:název-součásti-vysoké-školy">
        <div class="bh">Název součásti vysoké školy:</div>
        <div class="bv"><xsl:apply-templates/></div>
    </xsl:template>

    <xsl:template match="ak:odkaz_na_relevantní_vnitřní_předpisy">
        <div class="bh">Odkaz na relevantní vnitřní předpisy:</div>
        <div class="bv"><xsl:apply-templates/></div>
    </xsl:template>

    <xsl:template match="ak:A-I/ak:název-studijního-programu">
        <div class="bh">Název studijního programu:</div>
        <div class="bv"><xsl:apply-templates/></div>
    </xsl:template>

    <xsl:template name="normitem">
        <xsl:param name="label"/>
        <tr>
            <td class="th"><xsl:value-of select="$label"/></td>
            <td class="tv"><xsl:apply-templates/></td>
        </tr>
    </xsl:template>

    <xsl:template match="ak:B-I">
        <div class="section" head="B-I — Charakteristika studijního programu">
            <table class="section">
                <xsl:apply-templates/>
            </table>
        </div>
    </xsl:template>

    <xsl:template match="ak:B-I/ak:název-studijního-programu">
        <xsl:call-template name="normitem">
            <xsl:with-param name="label">Název studijního programu</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="ak:typ-studijního-programu">
        <xsl:call-template name="normitem">
            <xsl:with-param name="label">Typ studijního programu</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="ak:profil-studijního-programu">
        <xsl:call-template name="normitem">
            <xsl:with-param name="label">Profil studijního programu</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="ak:forma-studia">
        <xsl:call-template name="normitem">
            <xsl:with-param name="label">Forma studia</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="ak:garant-studijního-programu">
        <xsl:call-template name="normitem">
            <xsl:with-param name="label">Garant studijního programu</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="ak:rigorózní-řízení">
        <tr>
            <td class="th">Rigorózní řízení</td>
            <td style="padding:0;">
                <table class="partition">
                    <tr>
                        <td class="tv" style="width:20%;"><xsl:apply-templates/></td>
                        <td class="th" style="width:60%;">Udělovaný akademický titul</td>
                        <td class="tv" style="width:20%;"><xsl:value-of select="@titul"/></td>
                    </tr>
                </table>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="ak:*"></xsl:template>

    <!-- Šablona pro zpracování vnořených XHTML dokumentů -->
    <xsl:template match="xhtml:*">
        <xsl:element name="{local-name()}" namespace="http://www.w3.org/1999/xhtml">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>

    <!-- Šablona pro kopírování atributů -->
    <xsl:template match="@*">
        <xsl:attribute name="{local-name()}">
            <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>

</xsl:stylesheet>
