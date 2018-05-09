#!/usr/bin/perl -w

$ver = $ARGV[0]
print "ver=$ver\n";

$inputfile="data/$ver/repo/brand.txt";
open(IN,$inputfile);
while (<IN>)
{
	chomp;
	@token=split("\t");
	for ($i=0;$i<=$#token;$i++)
	{
		$brandtable{$token[$i]}=$token[0];
	}
}
close(IN);

$inputfile="data/$ver/repo/head.txt";
open(IN,$inputfile);
while (<IN>)
{
	chomp;
	$headtable{$_}=1;

}
close(IN);

$inputfile="data/$ver/repo/infix.lex";
open(IN,$inputfile);
while (<IN>)
{
	chomp;
	@token=split("\t");
	$infixtablea{$token[0]}=1;

}
close(IN);

$inputfile="data/$ver/repo/infix.txt";
open(IN,$inputfile);
while (<IN>)
{
	chomp;
	$infixtableb{$_}=1;

}
close(IN);

$count=0;
$inputfile="data/$ver/repo/product.txt";
open(IN,$inputfile);
while (<IN>)
{
	chomp;
	@token=split("\t");

	$id=$token[0];

	if (defined($brandtable{$token[1]}))
	{
		$brand=$brandtable{$token[1]};
	}
	else
	{
		die;
	}

	$item=$token[2];

	$ptableid{$id}->{"brand"}=$brand;
	$ptableid{$id}->{"item"}=$item;

	$ptablebrandid{$brand}->{$id}=$item;
	$ptablebranditem{$brand}->{$item}=$id;
	$ptablecount{$count}=$id;
	$count++;
}
close(IN);



$count=0;
$inputfile="data/$ver/repo/product.tag";
open(IN,$inputfile);
while (<IN>)
{
	chomp;
	$itemtag=$_;
	$id=$ptablecount{$count};
	$ptableid{$id}->{"itemtag"}=$itemtag;

	$item=$ptableid{$id}->{"item"};
	$itemtable{$item}=1;


	$itemtablea{$item}->{"itemtag"}=$itemtag;
	$headposition=-1;
	@token=split("　",$itemtag);
	for ($i=$#token;$i>=0;$i--)
	{
		if ($token[$i]=~/(.+)\((.+)\)/)
		{
			$word=$1;
			$postag=$2;
			if (defined($headtable{$word}))
			{
				$headposition=$i;
				$itemtablea{$item}->{"headposition"}=$headposition;
				last;
			}
		}
	}
	if ($headposition==-1)
	{
		die;
	}
	$count++;
}
close(IN);

$specifiedwordtable{"款"}=1;
$specifiedwordtable{"這款"}=1;
$specifiedwordtable{"一款"}=1;


$inputdir="data/$ver/article/parsed_article_parse/";
$tmpdir="data/$ver/article/parsed_article_parse1/";
$outputdir="data/$ver/xml/parsed_article_ws_pid/";

mkdir($tmpdir) unless(-d $tmpdir);
mkdir($outputdir) unless(-d $outputdir);

opendir(ID,$inputdir);
@dirset=sort readdir(ID);
foreach $dir (@dirset)
{
	$inputdir1=$inputdir.$dir."/";
	$tmpdir1=$tmpdir.$dir."/";
	$outputdir1=$outputdir.$dir."/";

	mkdir($tmpdir1) unless(-d $tmpdir1);
	mkdir($outputdir1) unless(-d $outputdir1);

	print "$inputdir1\n";
	opendir(ID1,$inputdir1);
	@fileset=sort readdir(ID1);
	foreach $file (@fileset)
	{
		if ($file!~/parse$/)
		{
			next;
		}

		$inputfile=$inputdir1.$file;

		if (not -f $inputfile)
		{
			next;
		}

		# $tmpfile=$inputfile."1";
		$tmpfile=$tmpdir1.$file."1";

		open(IN,$inputfile);
		open(OUT,">$tmpfile");
		while (<IN>)
		{
			chomp;
			$count=0;
			while (/\(.*\)/)
			{
				$_=~s/\(([^\(\)]*?)\)/<p$count>$1<\/p$count>/;
				$count++;
			}
			print OUT "$_\n";
			$number=$count;
		}
		close(IN);
		close(OUT);



		$count=0;
		$inputfile=$tmpfile;



		$wordcount=0;
		$brandrecord=();
		%contentrecord=();
		%breakrecord=();
		open(IN,$inputfile);
		while (<IN>)
		{
			chomp;
			@token=split(/\<\/?p[0-9]+\>|\|/);
			for ($i=0;$i<=$#token;$i++)
			{
				if ($token[$i]=~/(.+)\:(.+)\:(.+)/)
				{
					$role=$1;
					$postag=$2;
					$word=$3;
					$contentrecord{$wordcount}->{"role"}=$role;
					$contentrecord{$wordcount}->{"postag"}=$postag;
					$contentrecord{$wordcount}->{"word"}=$word;
					if (defined($brandtable{$word}))
					{
						$brand=$brandtable{$word};
						$brandrecord{$brand}=1;
					}
					$wordcount++;
				}
			}
			if (defined($breakrecord{$wordcount})){
				$breakrecord{$wordcount}++;
			} else {
				$breakrecord{$wordcount}=1;
			}
		}
		close(IN);
		$contentsize=$wordcount;

		# $outputfile=$inputfile.".label";
		use File::Basename;
		$file=basename($file, <".parse">).".xml";
		$outputfile=$outputdir1.$file;

		open(OUT,">$outputfile");
		%contenthead=();
		for ($i=0;$i<$contentsize;$i++)
		{
			if (defined($breakrecord{$i}))
			{
				if ($breakrecord{$i} != 1){
					print "$file $breakrecord{$i}\n";
				}
				for ($n=0;$n<$breakrecord{$i};$n++)
				{
					print OUT "\n";
				}
			}

			$id=-1;
			$word=$contentrecord{$i}->{"word"};
			$postag=$contentrecord{$i}->{"postag"};;

			# prule 1


			if (defined($itemtable{$word}))
			{


				$item=$word;
				$itemtag=$itemtablea{$item}->{"itemtag"};

				@brandset = keys %brandrecord;
				foreach $brand (@brandset)
				{
					if (defined($ptablebranditem{$brand}->{$item}))
					{

						if ($itemtag=~/　/)
						{
							$id=$ptablebranditem{$brand}->{$item};
						}
						else
						{
							if ($i>0 && $contentrecord{$i-1}->{"word"} eq $brand)
							{
								$id=$ptablebranditem{$brand}->{$item};
							}
						}
					}
				}

				$headposition=$itemtablea{$item}->{"headposition"};
				@token=split("　",$itemtag);
				for ($j=0;$j<=$#token;$j++)
				{
					if ($token[$j]=~/(.+)\((.+)\)/)
					{
						$internalword=$1;
						$internalpostag=$2;
						if ($j==$headposition)
						{
							$headword=$internalword;
							$headpostag=$internalpostag;
							if ($id>=0)
							{
									$contenthead{$headword}=$id;
									print OUT "　<product pid=\"$id\" gid=\"\" rule=\"P_rule1\">$headword($headpostag)</product>";
							}
							else
							{
									$brand="null";
								for ($k=$i;$k>=0 && $i-$k<=15;$k--)
								{
									$worda=$contentrecord{$k}->{"word"};
									if (defined($brandtable{$worda}))
									{
										$brand=$brandtable{$worda};
										last;
									}
								}

								$specifiedstate=0;
								for ($k=$i;$k>=0 && $i-$k<=15;$k--)
								{
									$worda=$contentrecord{$k}->{"word"};
									if (defined($specifiedwordtable{$worda}))
									{
										$specifiedstate=1;
										last;
									}
								}


								if ($brand ne "null" || $specifiedstate==1)
								{
									if ($brand ne "null")
									{
										print OUT "　<product pid=\"OSP\" gid=\"\" rule=\"OSP_rule1\">$headword($headpostag)</product>";
									}
									else
									{
											print OUT "　<product pid=\"OSP\" gid=\"\" rule=\"OSP_rule2\">$headword($headpostag)</product>";
									}
								}
								else
								{
									if (defined($contenthead{$headword}))
									{
										$id=$contenthead{$headword};
										print OUT "　<product pid=\"$id\" gid=\"\" rule=\"P_rule2\">$headword($headpostag)</product>";
									}
									else
									{
										print OUT "　<product pid=\"GP\" gid=\"\" rule=\"GP_rule1\">$headword($headpostag)</product>";
									}

								}
							}
						}
						else
						{
							print OUT "　$internalword($internalpostag)";
						}
					}
					else
					{
						die;
					}
				}
			}
			else
			{
				if (defined($headtable{$word}))
				{
					$headword=$word;
					$headpostag=$postag;

					$brand="null";
					for ($k=$i;$k>=0 && $i-$k<=20;$k--)
					{
						$worda=$contentrecord{$k}->{"word"};
						if (defined($brandtable{$worda}))
						{
							$brand=$brandtable{$worda};
							last;
						}
					}

					$specifiedstate=0;
					for ($k=$i;$k>=0 && $i-$k<=15;$k--)
					{
						$worda=$contentrecord{$k}->{"word"};
						if (defined($specifiedwordtable{$worda}))
						{
							$specifiedstate=1;
							last;
						}
					}

					if ($brand ne "null")
					{
						if (defined($contenthead{$headword}))
						{
							$id=$contenthead{$headword};
							if ($brand eq $ptableid{$id}->{"brand"})
							{
								print OUT "　<product pid=\"$id\" gid=\"\" rule=\"P_rule3\">$headword($headpostag)</product>";
							}
							else
							{
								print OUT "　<product pid=\"OSP\" gid=\"\" rule=\"OSP_rule3\">$headword($headpostag)</product>";
							}
						}
						else
						{
							print OUT "　<product pid=\"OSP\" gid=\"\" rule=\"OSP_rule4\">$headword($headpostag)</product>";
						}
					}
					else
					{
						if (defined($contenthead{$headword}))
						{
							$id=$contenthead{$headword};
							print OUT "　<product pid=\"$id\" gid=\"\" rule=\"P_rule4\">$headword($headpostag)</product>";
						}
						else
						{
							if ($specifiedstate==1)
							{
								print OUT "　<product pid=\"OSP\" gid=\"\" rule=\"OSP_rule5\">$headword($headpostag)</product>";
							}
							else
							{
								print OUT "　<product pid=\"GP\" gid=\"\" rule=\"GP_rule2\">$headword($headpostag)</product>";
							}
						}
					}
				}
				else
				{
					print OUT "　$word($postag)";
				}
			}
		}
		close(OUT);

		}
	}

